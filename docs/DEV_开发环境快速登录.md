# 开发环境快速登录 — 后端适配说明

## 一、现状分析

### APP 端已实现

`app/login.tsx` 在 `__DEV__` 模式下新增了「一键登录」功能，流程如下：

```
点击"一键登录 18910284131"
  → 调用 POST /api/v1/auth/sms/send  { phone: "18910284131" }
  → 从响应 message 字段中正则提取验证码（格式："验证码已发送（开发模式，验证码: 123456）"）
  → 调用 POST /api/v1/auth/sms/login { phone: "18910284131", code: "123456" }
  → 登录成功，自动导航
```

### 后端现状（已可用 ✅）

当 `sms_provider = "mock"`（当前默认值）时：

| 行为 | 说明 |
|------|------|
| 验证码生成 | 随机 6 位数字，存入 `sms_codes` 表 |
| 响应内容 | `message` 字段包含验证码明文 |
| 发送间隔 | 同一手机号 **60 秒** 内不可重复发送（429 错误） |
| 验证码有效期 | **5 分钟** |
| 验证方式 | 严格匹配数据库中未过期、未使用的记录 |

**结论：当前后端在 mock 模式下已能支持 APP 端的一键登录，无需改动即可工作。**

---

## 二、建议优化（提升开发体验）

虽然现有流程可用，但在频繁调试场景下存在以下痛点：

| 痛点 | 场景 | 影响 |
|------|------|------|
| 60 秒发送间隔 | 快速 登录→登出→登录 循环 | 需等待 60 秒才能再次发送验证码 |
| 依赖 message 解析 | 后端响应格式变化 | APP 正则匹配可能失败 |
| 每次验证码随机 | 无法预设固定测试凭据 | 自动化测试不稳定 |

### 优化方案：为测试手机号支持万能验证码

在 mock 模式下，对指定的测试手机号列表接受固定万能验证码（如 `000000`），同时放宽发送频率限制。

---

## 三、具体代码改动

### 3.1 `app/config.py` — 新增测试配置项

```python
# SMS Settings (短信验证码)
sms_provider: str = "mock"              # "mock" (dev) or "aliyun" / "tencent" (prod)
sms_code_length: int = 6               # 验证码位数
sms_code_expire_minutes: int = 5       # 验证码有效期
sms_send_interval_seconds: int = 60    # 同一手机号发送间隔

# ↓↓↓ 新增以下两项 ↓↓↓
sms_test_phones: list[str] = ["18910284131"]   # 测试手机号列表
sms_test_code: str = "000000"                   # 万能测试验证码
```

**说明：**
- `sms_test_phones`：允许使用万能验证码登录的手机号白名单
- `sms_test_code`：固定的万能验证码，仅在 `sms_provider == "mock"` 时生效
- 可通过环境变量 `SMS_TEST_PHONES` / `SMS_TEST_CODE` 覆盖默认值

### 3.2 `app/services/auth_service.py` — 修改验证逻辑

#### 3.2.1 `can_send_sms()` — 测试手机号跳过发送频率限制

```python
@staticmethod
async def can_send_sms(db: AsyncSession, phone: str) -> bool:
    """Check if enough time has passed since the last SMS to this phone."""
    # 测试手机号在 mock 模式下跳过频率限制
    if settings.sms_provider == "mock" and phone in settings.sms_test_phones:
        return True

    cutoff = datetime.utcnow() - timedelta(seconds=settings.sms_send_interval_seconds)
    result = await db.execute(
        select(SmsCode)
        .where(and_(SmsCode.phone == phone, SmsCode.created_at > cutoff))
        .order_by(SmsCode.created_at.desc())
        .limit(1)
    )
    recent = result.scalar_one_or_none()
    return recent is None
```

#### 3.2.2 `verify_sms_code()` — 测试手机号接受万能验证码

```python
@staticmethod
async def verify_sms_code(db: AsyncSession, phone: str, code: str) -> bool:
    """
    Verify a submitted SMS code.

    - In mock mode, test phones accept the universal test code.
    - Otherwise, finds the latest unused, non-expired code for this phone.
    - Marks it as used on success.
    """
    # 万能测试验证码（仅 mock 模式 + 白名单手机号）
    if (
        settings.sms_provider == "mock"
        and phone in settings.sms_test_phones
        and code == settings.sms_test_code
    ):
        return True

    now = datetime.utcnow()
    result = await db.execute(
        select(SmsCode)
        .where(
            and_(
                SmsCode.phone == phone,
                SmsCode.code == code,
                SmsCode.used == False,  # noqa: E712
                SmsCode.expires_at > now,
            )
        )
        .order_by(SmsCode.created_at.desc())
        .limit(1)
    )
    sms_record = result.scalar_one_or_none()
    if sms_record is None:
        return False

    # Mark as used
    sms_record.used = True
    await db.commit()
    return True
```

### 3.3 `app/api/auth.py` — 日志提示（可选）

在 `send_sms_code` 端点的响应中追加测试验证码提示：

```python
@router.post("/sms/send", response_model=SmsSendResponse)
async def send_sms_code(
    request: SmsSendRequest,
    db: AsyncSession = Depends(get_db),
):
    # Rate limit
    can_send = await auth_service.can_send_sms(db, request.phone)
    if not can_send:
        raise HTTPException(
            status_code=429,
            detail=f"请求过于频繁，请 {settings.sms_send_interval_seconds} 秒后再试",
        )

    code = await auth_service.send_sms_code(db, request.phone)

    # 构造 message
    if settings.sms_provider != "mock":
        message = "验证码已发送"
    elif request.phone in settings.sms_test_phones:
        message = f"验证码已发送（开发模式，验证码: {code}，万能码: {settings.sms_test_code}）"
    else:
        message = f"验证码已发送（开发模式，验证码: {code}）"

    return SmsSendResponse(
        success=True,
        message=message,
        expires_in=settings.sms_code_expire_minutes * 60,
    )
```

---

## 四、改动影响范围

| 文件 | 改动点 | 影响 |
|------|--------|------|
| `app/config.py` | 新增 `sms_test_phones`、`sms_test_code` | 仅新增配置项，默认值安全 |
| `app/services/auth_service.py` | `can_send_sms()` + `verify_sms_code()` | 仅在 `mock` 模式 + 白名单手机号时生效 |
| `app/api/auth.py` | 响应 `message` 字段格式微调 | 仅影响 mock 模式的提示文案 |

### 安全保障

- **三重保护条件**：必须同时满足 `sms_provider == "mock"` + 手机号在白名单中 + 验证码匹配万能码
- **生产环境不受影响**：生产环境 `sms_provider` 应设为 `"aliyun"` 或 `"tencent"`，此时所有测试逻辑完全跳过
- **无数据库副作用**：万能验证码验证直接返回 `True`，不产生数据库写入

---

## 五、APP 端配合改动（可选）

当后端完成上述改动后，APP 端的 `handleDevQuickLogin` 可进一步简化——跳过发送验证码步骤，直接用万能码登录：

```typescript
// app/login.tsx — 优化版 handleDevQuickLogin
const handleDevQuickLogin = useCallback(async () => {
  setError("");
  setDevLoading(true);
  try {
    // 直接用万能测试验证码登录，无需先发送
    await login(DEV_PHONE, "000000");
    if (router.canGoBack()) {
      router.back();
    } else {
      router.replace("/(tabs)/profile" as any);
    }
  } catch (err: any) {
    // 万能码不可用时，回退到原有的 发送→提取→登录 流程
    try {
      const result = await sendSmsCode({ phone: DEV_PHONE });
      const codeMatch = result.message.match(/验证码[：:]\s*(\d{4,6})/);
      if (codeMatch) {
        await login(DEV_PHONE, codeMatch[1]);
        if (router.canGoBack()) router.back();
        else router.replace("/(tabs)/profile" as any);
        return;
      }
    } catch {}
    setError(err.message || "快速登录失败");
  } finally {
    setDevLoading(false);
  }
}, [login, router]);
```

**优势：**
- 登录只需 1 次 API 请求（原来需要 2 次）
- 不受 60 秒发送间隔限制
- 不依赖 message 字段解析

---

## 六、验证清单

完成改动后，依次验证以下场景：

- [ ] mock 模式下，测试手机号使用万能码 `000000` 可直接登录
- [ ] mock 模式下，测试手机号连续快速登录（< 60 秒间隔）不报 429
- [ ] mock 模式下，非测试手机号仍需正常发码 + 验证流程
- [ ] mock 模式下，测试手机号使用错误验证码（如 `111111`）登录失败
- [ ] 将 `sms_provider` 改为 `"aliyun"` 后，测试手机号的万能码失效
- [ ] APP 端一键登录按钮完整流程正常工作

"""
AI Beauty Muse - LLM Service (OpenAI / Gemini)
Unified interface for text generation, image analysis, and image generation.

Supports switching between OpenAI and Gemini via the ``llm_provider`` config.
Gemini is called through its OpenAI-compatible endpoint, so the same ``openai``
Python SDK is used for both providers — no extra dependencies needed.

Image generation (DALL-E) always uses the OpenAI client regardless of provider.
Image editing supports two providers:
  - ``gpt-image-1``: OpenAI's image edit API with face-protection mask.
  - ``gemini``: Google Gemini native image editing (e.g. gemini-3-pro-image-preview)
    via the generateContent REST API.
"""
import io
import json
import base64
import asyncio
import httpx
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
from PIL import Image, ImageDraw, ImageFilter

from app.config import settings


def _build_http_client(proxy: Optional[str] = None) -> httpx.AsyncClient:
    """Build an httpx.AsyncClient with optional proxy for AsyncOpenAI."""
    if proxy:
        return httpx.AsyncClient(proxy=proxy)
    return httpx.AsyncClient()


class OpenAIService:
    """
    Unified LLM service that routes to OpenAI or Gemini based on config.

    All existing code imports ``openai_service`` from this module — the
    interface stays exactly the same regardless of which provider is active.
    """

    def __init__(self):
        """Initialize LLM client(s) based on ``settings.llm_provider``."""
        provider = settings.llm_provider.lower()
        proxy = settings.http_proxy or None

        if provider == "gemini":
            # ---- Gemini via OpenAI-compatible endpoint ----
            self.client = AsyncOpenAI(
                api_key=settings.gemini_api_key,
                base_url=settings.gemini_base_url,
                http_client=_build_http_client(proxy),
            )
            self.model = settings.gemini_model
            self.vision_model = settings.gemini_vision_model
            self._provider = "gemini"
        else:
            # ---- OpenAI (default) ----
            self.client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url if settings.openai_base_url else None,
                http_client=_build_http_client(proxy),
            )
            self.model = settings.openai_model
            self.vision_model = settings.openai_vision_model
            self._provider = "openai"

        # Image generation always uses OpenAI (DALL-E) — Gemini doesn't offer this.
        self._image_client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url if settings.openai_base_url else None,
            http_client=_build_http_client(proxy),
        )
        self.image_model = settings.openai_image_model
        self.image_edit_model = settings.openai_image_edit_model

        # Gemini native image editing settings
        self._gemini_api_key = settings.gemini_api_key
        self._gemini_image_edit_model = settings.gemini_image_edit_model

        # Gemini Pro client for destiny / fortune analysis
        self._gemini_destiny_client = AsyncOpenAI(
            api_key=settings.gemini_api_key,
            base_url=settings.gemini_base_url,
            http_client=_build_http_client(proxy),
        )
        self._gemini_destiny_model = settings.gemini_destiny_model

        self._default_edit_provider = settings.image_edit_provider
        self._http_proxy = proxy

        print(
            f"🤖 LLM provider: {self._provider}  model={self.model}  "
            f"vision={self.vision_model}  image={self.image_model}  "
            f"image_edit={self.image_edit_model}  "
            f"edit_provider={self._default_edit_provider}  "
            f"destiny_model={self._gemini_destiny_model}"
        )

    # ----------------------------------------------------------------
    # Text generation
    # ----------------------------------------------------------------

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        response_format: Optional[Dict] = None,
    ) -> str:
        """Generate text using chat completion (works with both providers)."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**kwargs)

        return response.choices[0].message.content

    # ----------------------------------------------------------------
    # Destiny / Fortune text generation (Gemini 3 Pro)
    # ----------------------------------------------------------------

    async def generate_destiny_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> str:
        """Generate destiny / fortune text using Gemini 3 Pro.

        This always routes to the ``gemini_destiny_model`` regardless of
        the ``llm_provider`` setting, because fortune-telling requires the
        stronger reasoning and richer cultural knowledge of the Pro model.
        """
        messages: List[Dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self._gemini_destiny_client.chat.completions.create(
            model=self._gemini_destiny_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    # ----------------------------------------------------------------
    # Image analysis (vision)
    # ----------------------------------------------------------------

    async def analyze_image(
        self,
        image_url: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Analyze an image using the vision model.

        ``image_url`` can be a regular URL *or* a base64 data URI
        (``data:image/jpeg;base64,...``).  Both OpenAI and Gemini's
        OpenAI-compatible endpoint accept this format.
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        })

        response = await self.client.chat.completions.create(
            model=self.vision_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content

    # ----------------------------------------------------------------
    # Image generation (DALL-E — always OpenAI)
    # ----------------------------------------------------------------

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "natural",
    ) -> str:
        """Generate an image using DALL-E (always routed to OpenAI)."""
        response = await self._image_client.images.generate(
            model=self.image_model,
            prompt=prompt,
            size=size,
            quality=quality,
            style=style,
            n=1,
        )

        return response.data[0].url

    # ----------------------------------------------------------------
    # Image editing (gpt-image-1 + face-protecting mask)
    # ----------------------------------------------------------------

    _EDIT_PROMPT = (
        "Hair-only inpainting edit.  "
        "Change the hair in the transparent (editable) region to: {instructions}.  "
        "The masked (opaque) areas — face, body, background — are locked "
        "and must remain pixel-identical to the original photo.  "
        "Blend the new hair naturally at the hairline.  "
        "Photorealistic result, same person, same lighting."
    )

    # ---- Language helpers ------------------------------------------------

    @staticmethod
    def _needs_translation(text: str) -> bool:
        """Return ``True`` when *text* has a significant non-ASCII share."""
        non_ascii = sum(1 for ch in text if ord(ch) > 127)
        return non_ascii / max(len(text), 1) > 0.15

    async def _translate_to_english(self, text: str) -> str:
        """Translate hair-styling description to English via LLM."""
        translated = await self.generate_text(
            prompt=(
                "Translate the following hairstyle / hair color description "
                "into clear, concise English.  Keep professional hairdressing "
                "terminology accurate.  Return ONLY the translation.\n\n"
                f"{text}"
            ),
            system_prompt=(
                "You are a professional translator specialising in "
                "hairdressing and beauty terminology."
            ),
            temperature=0.2,
            max_tokens=500,
        )
        return translated.strip()

    # ---- Size helper ----------------------------------------------------

    @staticmethod
    def _best_output_size(image_bytes: bytes) -> str:
        """Pick ``images.edit`` size matching the original aspect ratio."""
        img = Image.open(io.BytesIO(image_bytes))
        w, h = img.size
        ratio = w / h
        if ratio > 1.2:
            return "1536x1024"   # landscape
        elif ratio < 0.83:
            return "1024x1536"   # portrait
        return "1024x1024"       # roughly square

    # ---- Face detection (vision) ----------------------------------------

    async def _detect_face_bounds(
        self, image_bytes: bytes, content_type: str,
    ) -> Optional[Dict[str, float]]:
        """Ask the vision model for the face bounding box (% of image).

        Returns ``{"top": N, "bottom": N, "left": N, "right": N}``
        where each value is 0-100, or ``None`` on failure.
        """
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_uri = f"data:{content_type};base64,{b64}"

        try:
            resp_text = await self.analyze_image(
                image_url=data_uri,
                prompt=(
                    "Locate the face in this portrait photo.\n"
                    "Return ONLY a JSON object with the bounding box "
                    "as percentages (0-100) of the image dimensions:\n"
                    '{"top": N, "bottom": N, "left": N, "right": N}\n'
                    "top = hairline (where forehead skin begins)\n"
                    "bottom = chin bottom\n"
                    "left = left ear outer edge\n"
                    "right = right ear outer edge\n"
                    "Return ONLY the JSON. No explanation."
                ),
                system_prompt="Face bounding-box detector. Output valid JSON only.",
                temperature=0.1,
                max_tokens=120,
            )
            # Strip markdown fences if present
            txt = resp_text.strip()
            if "```" in txt:
                txt = txt.split("```")[1]
                if txt.startswith("json"):
                    txt = txt[4:]
                txt = txt.split("```")[0]
            bounds = json.loads(txt.strip())
            for key in ("top", "bottom", "left", "right"):
                val = float(bounds[key])
                if not (0 <= val <= 100):
                    return None
                bounds[key] = val
            return bounds
        except Exception:
            return None

    # ---- Mask generation (Pillow) ---------------------------------------

    @staticmethod
    def _create_hair_mask(
        image_bytes: bytes,
        face: Dict[str, float],
    ) -> io.BytesIO:
        """Build a PNG mask for ``images.edit``.

        - **Opaque** (alpha 255) = protected (face, body, background)
        - **Transparent** (alpha 0) = editable (hair region)

        The mask starts fully opaque, then carves out a transparent
        "hair dome" above and beside the face, re-protecting the
        face itself with an opaque ellipse.
        """
        img = Image.open(io.BytesIO(image_bytes))
        w, h = img.size

        # Face bounds in pixels
        ft = int(face["top"] / 100 * h)
        fb = int(face["bottom"] / 100 * h)
        fl = int(face["left"] / 100 * w)
        fr = int(face["right"] / 100 * w)
        face_w = fr - fl
        face_h = fb - ft

        # ---- Build alpha channel (255 = keep, 0 = edit) ----
        alpha = Image.new("L", (w, h), 255)
        draw = ImageDraw.Draw(alpha)

        # 1) Top strip: from top of image to just below hairline
        #    → makes the entire top area (sky / hair above head) editable
        hairline_y = ft + int(face_h * 0.08)
        draw.rectangle([0, 0, w, hairline_y], fill=0)

        # 2) Side strips: image edge → face edge, from top down to chin
        #    → makes hair on the sides editable
        side_pad = int(face_w * 0.05)  # tiny inward overlap
        draw.rectangle([0, 0, fl + side_pad, fb], fill=0)           # left
        draw.rectangle([fr - side_pad, 0, w, fb], fill=0)           # right

        # 3) Re-protect the face with a generous opaque ellipse
        pad_x = int(face_w * 0.12)
        pad_top = int(face_h * 0.06)
        pad_bot = int(face_h * 0.08)
        draw.ellipse(
            [fl - pad_x, ft - pad_top, fr + pad_x, fb + pad_bot],
            fill=255,
        )

        # 4) Re-protect body: everything below chin stays opaque
        draw.rectangle([0, fb - int(face_h * 0.05), w, h], fill=255)

        # Gaussian blur for soft hairline blending (avoid hard seam)
        blur_r = max(face_w // 12, 6)
        alpha = alpha.filter(ImageFilter.GaussianBlur(radius=blur_r))

        # Assemble RGBA mask
        mask_img = Image.new("RGBA", (w, h), (0, 0, 0, 255))
        mask_img.putalpha(alpha)

        buf = io.BytesIO()
        mask_img.save(buf, format="PNG")
        buf.seek(0)
        buf.name = "mask.png"
        return buf

    # ---- Main edit entry point (dispatcher) --------------------------------

    async def edit_image(
        self,
        image_bytes: bytes,
        content_type: str,
        instructions: str,
        size: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> bytes:
        """
        Hair-only image editing — dispatches to the selected provider.

        Parameters
        ----------
        provider : str or None
            ``"gpt-image-1"`` — OpenAI images.edit with face-protection mask.
            ``"gemini"``       — Gemini native image editing (generateContent).
            When *None*, falls back to ``settings.image_edit_provider``.

        Returns raw PNG/image bytes of the edited image.
        """
        provider = (provider or self._default_edit_provider).lower().strip()

        if provider in ("gpt-image-1", "openai"):
            return await self._edit_image_gpt(image_bytes, content_type, instructions, size)
        elif provider == "gemini":
            return await self._edit_image_gemini(image_bytes, content_type, instructions)
        else:
            raise ValueError(
                f"Unknown image edit provider: '{provider}'. "
                f"Supported: 'gpt-image-1', 'gemini'."
            )

    # ---- Provider: gpt-image-1 (OpenAI) ----------------------------------

    async def _edit_image_gpt(
        self,
        image_bytes: bytes,
        content_type: str,
        instructions: str,
        size: Optional[str] = None,
    ) -> bytes:
        """
        Hair-only image editing via OpenAI ``images.edit`` (gpt-image-1)
        with automatic face-protection mask.
        """
        # 1) Translate if needed
        if self._needs_translation(instructions):
            instructions = await self._translate_to_english(instructions)

        # 2) Auto-detect output size
        if size is None:
            size = self._best_output_size(image_bytes)

        # 3) Detect face and build mask
        face_bounds = await self._detect_face_bounds(image_bytes, content_type)
        mask_file: Optional[io.BytesIO] = None
        if face_bounds is not None:
            mask_file = self._create_hair_mask(image_bytes, face_bounds)

        # 4) Prepare image file
        ext_map = {
            "image/jpeg": "photo.jpg",
            "image/png": "photo.png",
            "image/webp": "photo.webp",
        }
        image_file = io.BytesIO(image_bytes)
        image_file.name = ext_map.get(content_type, "photo.png")

        # 5) Build prompt
        prompt = self._EDIT_PROMPT.format(instructions=instructions)

        # 6) Call images.edit
        kwargs: Dict[str, Any] = {
            "model": self.image_edit_model,
            "image": image_file,
            "prompt": prompt,
            "n": 1,
            "size": size,
        }
        if mask_file is not None:
            kwargs["mask"] = mask_file

        response = await self._image_client.images.edit(**kwargs)

        # 7) Extract result bytes
        data = response.data[0]
        if getattr(data, "b64_json", None):
            return base64.b64decode(data.b64_json)
        elif getattr(data, "url", None):
            async with httpx.AsyncClient(timeout=60, proxy=self._http_proxy) as client:
                resp = await client.get(data.url)
                resp.raise_for_status()
                return resp.content
        else:
            raise ValueError("No image data in API response")

    # ---- Provider: Gemini native image editing ---------------------------

    _GEMINI_API = "https://generativelanguage.googleapis.com/v1beta"

    _GEMINI_EDIT_PROMPT = (
        "You are a professional photo retoucher.  "
        "Edit ONLY the hair in this photo according to the instructions below.  "
        "You MUST keep the person's face, facial features, expression, skin, "
        "body, clothing, background, and lighting EXACTLY the same.  "
        "Only the hairstyle and/or hair color should change.\n\n"
        "Instructions: {instructions}\n\n"
        "Output a single photorealistic image — same person, same pose, "
        "only the hair has been changed."
    )

    async def _edit_image_gemini(
        self,
        image_bytes: bytes,
        content_type: str,
        instructions: str,
    ) -> bytes:
        """
        Hair-only image editing via **Gemini** native ``generateContent`` API.

        Uses models like ``gemini-3-pro-image-preview`` that support
        multimodal input (text + image) and image output via the
        ``responseModalities`` config.

        Flow:
        1. Translate non-English instructions.
        2. POST image + prompt to Gemini ``generateContent`` endpoint.
        3. Extract the output image bytes from ``inlineData`` in the
           response parts.
        """
        if not self._gemini_api_key:
            raise ValueError(
                "Gemini API key is not configured.  "
                "Set the GEMINI_API_KEY environment variable."
            )

        # 1) Translate if needed
        if self._needs_translation(instructions):
            instructions = await self._translate_to_english(instructions)

        # 2) Build prompt
        prompt_text = self._GEMINI_EDIT_PROMPT.format(instructions=instructions)

        # 3) Encode image as base64
        b64_image = base64.b64encode(image_bytes).decode()

        # 4) Build request payload for generateContent
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt_text},
                        {
                            "inlineData": {
                                "mimeType": content_type,
                                "data": b64_image,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "responseModalities": ["IMAGE", "TEXT"],
                "temperature": 0.4,
            },
        }

        url = (
            f"{self._GEMINI_API}/models/{self._gemini_image_edit_model}"
            f":generateContent?key={self._gemini_api_key}"
        )

        async with httpx.AsyncClient(timeout=180, proxy=self._http_proxy) as http:
            resp = await http.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            result = resp.json()

        # 5) Extract image from response
        candidates = result.get("candidates", [])
        if not candidates:
            error_msg = result.get("error", {}).get("message", "No candidates returned")
            raise ValueError(f"Gemini image editing failed: {error_msg}")

        parts = candidates[0].get("content", {}).get("parts", [])
        for part in parts:
            inline = part.get("inlineData")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])

        # If no image part found, report what we got
        text_parts = [p.get("text", "") for p in parts if "text" in p]
        raise ValueError(
            "Gemini returned no image in response. "
            f"Text response: {''.join(text_parts)[:500]}"
        )

    # ---- Edit image by reference (portrait + hairstyle reference image) ----

    _GEMINI_EDIT_BY_REFERENCE_PROMPT = (
        "You are a professional salon retoucher. You will receive TWO images.\n\n"
        "IMAGE 1 = The portrait (the person whose hair you will replace).\n"
        "IMAGE 2 = The hairstyle reference (the exact hairstyle to copy onto the person in Image 1).\n\n"
        "TASK: Replace the hair in Image 1 with the hairstyle from Image 2. The result must look as if "
        "the person in Image 1 went to the salon and got the exact same hairstyle as in Image 2.\n\n"
        "You MUST copy the reference (Image 2) as closely as possible:\n"
        "- Hair length (short / medium / long) must match the reference.\n"
        "- Hair color and tone must match the reference.\n"
        "- Curl, wave, or straight texture must match the reference.\n"
        "- Bangs style (none / side-swept / straight / curtain etc.) must match the reference.\n"
        "- Layering, volume, and parting must match the reference.\n"
        "- Do not simplify or reinterpret: replicate the reference hairstyle in detail.\n\n"
        "You MUST keep unchanged: the face, facial features, expression, skin tone, body, clothing, "
        "background, and lighting of the person in Image 1. Only the hair region is replaced.\n\n"
        "Output a single photorealistic image: the same person and pose as Image 1, with the hairstyle "
        "from Image 2 applied faithfully."
    )

    def _normalize_image_mime(self, content_type: Optional[str]) -> str:
        """Ensure MIME type is valid for Gemini (e.g. image/jpg -> image/jpeg)."""
        if not content_type or content_type.strip() == "":
            return "image/jpeg"
        ct = content_type.split(";")[0].strip().lower()
        if ct == "image/jpg":
            return "image/jpeg"
        if ct not in ("image/jpeg", "image/png", "image/webp"):
            return "image/jpeg"
        return ct

    def _prepare_image_for_gemini(
        self, image_bytes: bytes, content_type: str, max_size: int = 1536, quality: int = 88
    ) -> tuple[bytes, str]:
        """
        Resize and compress image so the request stays within Gemini limits.
        Returns (jpeg_bytes, "image/jpeg").
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img = img.convert("RGB")
        except Exception as e:
            raise ValueError(f"Invalid image file: {e}") from e
        w, h = img.size
        if max(w, h) > max_size:
            ratio = max_size / max(w, h)
            new_w, new_h = int(w * ratio), int(h * ratio)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue(), "image/jpeg"

    async def edit_image_by_reference(
        self,
        image_bytes: bytes,
        content_type: str,
        reference_image_bytes: bytes,
        reference_content_type: str,
    ) -> bytes:
        """
        Transfer hairstyle from a reference image to the portrait. Uses Gemini
        generateContent with two images (portrait + reference). Returns raw
        image bytes of the edited photo.
        """
        if not self._gemini_api_key:
            raise ValueError(
                "Gemini API key is not configured. "
                "Face-edit-by-reference requires Gemini. Set GEMINI_API_KEY."
            )

        mime1 = self._normalize_image_mime(content_type)
        mime2 = self._normalize_image_mime(reference_content_type)

        # Resize/compress to stay within Gemini size limits and avoid 400
        try:
            portrait_bytes, mime1 = self._prepare_image_for_gemini(image_bytes, mime1)
            ref_bytes, mime2 = self._prepare_image_for_gemini(reference_image_bytes, mime2)
        except ValueError as e:
            raise e

        b64_portrait = base64.b64encode(portrait_bytes).decode()
        b64_ref = base64.b64encode(ref_bytes).decode()

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": self._GEMINI_EDIT_BY_REFERENCE_PROMPT},
                        {
                            "inlineData": {
                                "mimeType": mime1,
                                "data": b64_portrait,
                            }
                        },
                        {
                            "inlineData": {
                                "mimeType": mime2,
                                "data": b64_ref,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "responseModalities": ["IMAGE", "TEXT"],
                "temperature": 0.25,
            },
        }

        url = (
            f"{self._GEMINI_API}/models/{self._gemini_image_edit_model}"
            f":generateContent?key={self._gemini_api_key}"
        )

        last_error: Optional[str] = None
        max_retries = 3
        base_delay = 3

        for attempt in range(max_retries):
            async with httpx.AsyncClient(timeout=180, proxy=self._http_proxy) as http:
                resp = await http.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )

            if resp.status_code == 200:
                result = resp.json()
                break

            try:
                err_body = resp.json()
                msg = err_body.get("error", {}).get("message", resp.text[:500])
            except Exception:
                msg = resp.text[:500] if resp.text else f"HTTP {resp.status_code}"
            last_error = f"Gemini API error: {msg}"

            # Retry on rate limit / high demand (429, 503 or message contains "high demand"/"try again")
            should_retry = (
                resp.status_code in (429, 503)
                or "high demand" in msg.lower()
                or "try again" in msg.lower()
            )
            if should_retry and attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                await asyncio.sleep(delay)
                continue
            raise ValueError(last_error)

        # Check for promptFeedback block (safety, etc.)
        prompt_feedback = result.get("promptFeedback", {})
        if prompt_feedback:
            block_reason = prompt_feedback.get("blockReason")
            if block_reason:
                raise ValueError(
                    f"Gemini blocked the request: {block_reason}. "
                    "Try different images or check content policy."
                )

        candidates = result.get("candidates", [])
        if not candidates:
            error_msg = result.get("error", {}).get("message", "No candidates returned")
            raise ValueError(f"Gemini edit-by-reference failed: {error_msg}")

        c0 = candidates[0]
        if c0.get("finishReason") and c0["finishReason"] not in ("STOP", "MAX_TOKENS"):
            raise ValueError(
                f"Gemini finished with reason: {c0.get('finishReason', 'UNKNOWN')}. "
                "Content may have been filtered."
            )

        parts = c0.get("content", {}).get("parts", [])
        for part in parts:
            inline = part.get("inlineData")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"])

        text_parts = [p.get("text", "") for p in parts if "text" in p]
        raise ValueError(
            "Gemini returned no image in response. "
            f"Text response: {''.join(text_parts)[:500]}"
        )

    # ----------------------------------------------------------------
    # Beauty reference image generation (Gemini text-to-image)
    # ----------------------------------------------------------------

    async def generate_beauty_image(self, prompt: str) -> Optional[bytes]:
        """Generate a beauty reference / mood-board image via Gemini native API.

        Uses the same ``generateContent`` endpoint as image editing but
        with text-only input.  Returns raw image bytes on success or
        ``None`` on any failure (best-effort).
        """
        if not self._gemini_api_key:
            return None

        payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ],
            "generationConfig": {
                "responseModalities": ["IMAGE", "TEXT"],
                "temperature": 0.8,
            },
        }

        url = (
            f"{self._GEMINI_API}/models/{self._gemini_image_edit_model}"
            f":generateContent?key={self._gemini_api_key}"
        )

        try:
            async with httpx.AsyncClient(timeout=120, proxy=self._http_proxy) as http:
                resp = await http.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )
                resp.raise_for_status()
                result = resp.json()

            candidates = result.get("candidates", [])
            if not candidates:
                return None

            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                inline = part.get("inlineData")
                if inline and inline.get("data"):
                    return base64.b64decode(inline["data"])

            return None
        except Exception as e:
            print(f"⚠️ Beauty image generation failed: {e}")
            return None

    # ----------------------------------------------------------------
    # Chat with context
    # ----------------------------------------------------------------

    async def chat_with_context(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        image_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Chat with conversation history and optional image context."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })

        # Add current message with optional image
        if image_url:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": message},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            })
        else:
            messages.append({"role": "user", "content": message})

        response = await self.client.chat.completions.create(
            model=self.vision_model if image_url else self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
        )

        return response.choices[0].message.content


# Singleton instance — all services import this
openai_service = OpenAIService()

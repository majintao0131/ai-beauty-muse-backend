"""
AI Beauty Muse - Destiny/BaZi Service
Handles Chinese astrology calculations including BaZi (八字) and Five Elements (五行).
"""
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


# 天干 (Heavenly Stems)
HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 地支 (Earthly Branches)
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 天干對應五行
STEM_ELEMENTS = {
    "甲": "wood", "乙": "wood",
    "丙": "fire", "丁": "fire",
    "戊": "earth", "己": "earth",
    "庚": "metal", "辛": "metal",
    "壬": "water", "癸": "water",
}

# 地支對應五行
BRANCH_ELEMENTS = {
    "子": "water", "丑": "earth", "寅": "wood", "卯": "wood",
    "辰": "earth", "巳": "fire", "午": "fire", "未": "earth",
    "申": "metal", "酉": "metal", "戌": "earth", "亥": "water",
}

# 五行中文名
ELEMENT_NAMES = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}

# 五行相生
ELEMENT_GENERATE = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}

# 五行相剋
ELEMENT_OVERCOME = {
    "wood": "earth",
    "fire": "metal",
    "earth": "water",
    "metal": "wood",
    "water": "fire",
}

# 五行對應顏色
ELEMENT_COLORS = {
    "wood": [
        {"name": "森林綠", "hex": "#228B22"},
        {"name": "翠綠", "hex": "#00FF7F"},
        {"name": "青色", "hex": "#00CED1"},
        {"name": "橄欖綠", "hex": "#808000"},
    ],
    "fire": [
        {"name": "正紅", "hex": "#FF0000"},
        {"name": "橙紅", "hex": "#FF4500"},
        {"name": "紫紅", "hex": "#C71585"},
        {"name": "珊瑚紅", "hex": "#FF7F50"},
    ],
    "earth": [
        {"name": "土黃", "hex": "#DAA520"},
        {"name": "駝色", "hex": "#C19A6B"},
        {"name": "咖啡色", "hex": "#6F4E37"},
        {"name": "米色", "hex": "#F5F5DC"},
    ],
    "metal": [
        {"name": "純白", "hex": "#FFFFFF"},
        {"name": "銀色", "hex": "#C0C0C0"},
        {"name": "香檳金", "hex": "#F7E7CE"},
        {"name": "淺灰", "hex": "#D3D3D3"},
    ],
    "water": [
        {"name": "深藍", "hex": "#00008B"},
        {"name": "黑色", "hex": "#000000"},
        {"name": "藏青", "hex": "#191970"},
        {"name": "靛藍", "hex": "#4B0082"},
    ],
}

# 時辰對應地支
HOUR_TO_BRANCH = {
    (23, 0): "子", (1, 2): "丑", (3, 4): "寅", (5, 6): "卯",
    (7, 8): "辰", (9, 10): "巳", (11, 12): "午", (13, 14): "未",
    (15, 16): "申", (17, 18): "酉", (19, 20): "戌", (21, 22): "亥",
}


@dataclass
class BaziPillar:
    """A single pillar in BaZi chart."""
    heavenly: str
    earthly: str
    
    @property
    def element(self) -> str:
        """Get the primary element of this pillar."""
        return STEM_ELEMENTS.get(self.heavenly, "earth")


class DestinyService:
    """Service for Chinese astrology calculations."""
    
    def __init__(self):
        """Initialize the destiny service."""
        pass
    
    def calculate_year_pillar(self, year: int) -> BaziPillar:
        """
        Calculate the year pillar (年柱).
        
        Args:
            year: Birth year
            
        Returns:
            BaziPillar for the year
        """
        # 以1984年甲子年為基準
        base_year = 1984
        diff = year - base_year
        
        stem_index = diff % 10
        branch_index = diff % 12
        
        # 處理負數
        if stem_index < 0:
            stem_index += 10
        if branch_index < 0:
            branch_index += 12
        
        return BaziPillar(
            heavenly=HEAVENLY_STEMS[stem_index],
            earthly=EARTHLY_BRANCHES[branch_index],
        )
    
    def calculate_month_pillar(self, year: int, month: int) -> BaziPillar:
        """
        Calculate the month pillar (月柱).
        
        Args:
            year: Birth year
            month: Birth month (1-12)
            
        Returns:
            BaziPillar for the month
        """
        year_pillar = self.calculate_year_pillar(year)
        year_stem_index = HEAVENLY_STEMS.index(year_pillar.heavenly)
        
        # 月支從寅開始（正月）
        month_branch_index = (month + 1) % 12
        
        # 根據年干推算月干
        # 甲己之年丙作首，乙庚之歲戊為頭
        # 丙辛之歲庚為首，丁壬之歲壬為頭
        # 戊癸之歲甲為首
        month_stem_base = [2, 4, 6, 8, 0]  # 丙、戊、庚、壬、甲
        base = month_stem_base[year_stem_index % 5]
        month_stem_index = (base + month - 1) % 10
        
        return BaziPillar(
            heavenly=HEAVENLY_STEMS[month_stem_index],
            earthly=EARTHLY_BRANCHES[month_branch_index],
        )
    
    def calculate_day_pillar(self, year: int, month: int, day: int) -> BaziPillar:
        """
        Calculate the day pillar (日柱).
        
        Args:
            year: Birth year
            month: Birth month
            day: Birth day
            
        Returns:
            BaziPillar for the day
        """
        # 使用簡化的日柱計算公式
        # 以2000年1月1日為基準（甲午日）
        base_date = date(2000, 1, 1)
        target_date = date(year, month, day)
        
        diff = (target_date - base_date).days
        
        # 2000年1月1日是甲午日
        base_stem = 0  # 甲
        base_branch = 6  # 午
        
        stem_index = (base_stem + diff) % 10
        branch_index = (base_branch + diff) % 12
        
        if stem_index < 0:
            stem_index += 10
        if branch_index < 0:
            branch_index += 12
        
        return BaziPillar(
            heavenly=HEAVENLY_STEMS[stem_index],
            earthly=EARTHLY_BRANCHES[branch_index],
        )
    
    def calculate_hour_pillar(self, year: int, month: int, day: int, hour: int) -> BaziPillar:
        """
        Calculate the hour pillar (時柱).
        
        Args:
            year: Birth year
            month: Birth month
            day: Birth day
            hour: Birth hour (0-23)
            
        Returns:
            BaziPillar for the hour
        """
        day_pillar = self.calculate_day_pillar(year, month, day)
        day_stem_index = HEAVENLY_STEMS.index(day_pillar.heavenly)
        
        # 計算時支
        if hour == 23 or hour == 0:
            hour_branch_index = 0  # 子時
        else:
            hour_branch_index = (hour + 1) // 2
        
        # 根據日干推算時干
        # 甲己還加甲，乙庚丙作初
        # 丙辛從戊起，丁壬庚子居
        # 戊癸何方發，壬子是真途
        hour_stem_base = [0, 2, 4, 6, 8]  # 甲、丙、戊、庚、壬
        base = hour_stem_base[day_stem_index % 5]
        hour_stem_index = (base + hour_branch_index) % 10
        
        return BaziPillar(
            heavenly=HEAVENLY_STEMS[hour_stem_index],
            earthly=EARTHLY_BRANCHES[hour_branch_index],
        )
    
    def calculate_bazi(
        self,
        year: int,
        month: int,
        day: int,
        hour: Optional[int] = None,
    ) -> List[BaziPillar]:
        """
        Calculate complete BaZi (四柱八字).
        
        Args:
            year: Birth year
            month: Birth month
            day: Birth day
            hour: Birth hour (optional)
            
        Returns:
            List of four BaziPillars [年柱, 月柱, 日柱, 時柱]
        """
        pillars = [
            self.calculate_year_pillar(year),
            self.calculate_month_pillar(year, month),
            self.calculate_day_pillar(year, month, day),
        ]
        
        if hour is not None:
            pillars.append(self.calculate_hour_pillar(year, month, day, hour))
        else:
            # 如果沒有時辰，用問號表示
            pillars.append(BaziPillar(heavenly="?", earthly="?"))
        
        return pillars
    
    def count_five_elements(self, pillars: List[BaziPillar]) -> Dict[str, int]:
        """
        Count the distribution of five elements in BaZi.
        
        Args:
            pillars: List of BaziPillars
            
        Returns:
            Dictionary with element counts
        """
        counts = {"wood": 0, "fire": 0, "earth": 0, "metal": 0, "water": 0}
        
        for pillar in pillars:
            if pillar.heavenly != "?":
                element = STEM_ELEMENTS.get(pillar.heavenly)
                if element:
                    counts[element] += 1
            
            if pillar.earthly != "?":
                element = BRANCH_ELEMENTS.get(pillar.earthly)
                if element:
                    counts[element] += 1
        
        return counts
    
    def analyze_day_master(self, pillars: List[BaziPillar]) -> Tuple[str, str]:
        """
        Analyze the day master (日主) strength.
        
        Args:
            pillars: List of BaziPillars
            
        Returns:
            Tuple of (day_master_element, strength_analysis)
        """
        day_pillar = pillars[2]
        day_master_element = STEM_ELEMENTS.get(day_pillar.heavenly, "earth")
        day_master_cn = ELEMENT_NAMES.get(day_master_element, "土")
        
        # 計算五行分布
        counts = self.count_five_elements(pillars)
        
        # 計算日主得分（簡化版本）
        # 同類五行和生我五行加分
        generating_element = [k for k, v in ELEMENT_GENERATE.items() if v == day_master_element][0]
        
        support_score = counts[day_master_element] + counts[generating_element]
        total_score = sum(counts.values())
        
        if support_score >= total_score / 2:
            strength = "旺"
            analysis = f"日主{day_master_cn}得令得地，身強有力。適合穿著能洩秀的顏色，展現自信魅力。"
        else:
            strength = "弱"
            analysis = f"日主{day_master_cn}力量稍弱，需要補充能量。適合穿著生扶日主的顏色，增強氣場。"
        
        return f"{day_pillar.heavenly}{day_master_cn}（{strength}）", analysis
    
    def get_favorable_element(self, pillars: List[BaziPillar]) -> str:
        """
        Determine the favorable element (喜用神).
        
        Args:
            pillars: List of BaziPillars
            
        Returns:
            Favorable element name
        """
        day_pillar = pillars[2]
        day_master_element = STEM_ELEMENTS.get(day_pillar.heavenly, "earth")
        
        counts = self.count_five_elements(pillars)
        generating_element = [k for k, v in ELEMENT_GENERATE.items() if v == day_master_element][0]
        
        support_score = counts[day_master_element] + counts[generating_element]
        total_score = sum(counts.values())
        
        if support_score >= total_score / 2:
            # 身強，喜洩秀或克制
            favorable = ELEMENT_GENERATE.get(day_master_element)
        else:
            # 身弱，喜生扶
            favorable = generating_element
        
        return ELEMENT_NAMES.get(favorable, "土")
    
    def get_color_recommendations(
        self,
        pillars: List[BaziPillar],
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Get color recommendations based on BaZi.
        
        Args:
            pillars: List of BaziPillars
            
        Returns:
            Tuple of (enhance_colors, balance_colors, avoid_colors)
        """
        counts = self.count_five_elements(pillars)
        day_pillar = pillars[2]
        day_master_element = STEM_ELEMENTS.get(day_pillar.heavenly, "earth")
        
        # 找出缺失或最弱的五行
        min_element = min(counts, key=counts.get)
        max_element = max(counts, key=counts.get)
        
        # 補能色：補充缺失的五行
        enhance_colors = []
        for color in ELEMENT_COLORS.get(min_element, [])[:2]:
            enhance_colors.append({**color, "element": min_element})
        
        # 平衡色：洩掉過旺的五行
        balance_element = ELEMENT_GENERATE.get(max_element, "earth")
        balance_colors = []
        for color in ELEMENT_COLORS.get(balance_element, [])[:2]:
            balance_colors.append({**color, "element": balance_element})
        
        # 禁忌色：克制日主的五行
        avoid_element = ELEMENT_OVERCOME.get(day_master_element, "earth")
        avoid_colors = []
        for color in ELEMENT_COLORS.get(avoid_element, [])[:2]:
            avoid_colors.append({**color, "element": avoid_element})
        
        return enhance_colors, balance_colors, avoid_colors
    
    def get_today_stem_branch(self) -> str:
        """
        Get today's heavenly stem and earthly branch.
        
        Returns:
            Today's stem and branch as string
        """
        today = date.today()
        pillar = self.calculate_day_pillar(today.year, today.month, today.day)
        return f"{pillar.heavenly}{pillar.earthly}"
    
    def get_today_element(self) -> str:
        """
        Get today's dominant element.
        
        Returns:
            Today's element name in Chinese
        """
        today = date.today()
        pillar = self.calculate_day_pillar(today.year, today.month, today.day)
        element = STEM_ELEMENTS.get(pillar.heavenly, "earth")
        return ELEMENT_NAMES.get(element, "土")
    
    def get_today_lucky_colors(self) -> List[Dict]:
        """
        Get today's lucky colors based on the day's element.
        
        Returns:
            List of lucky colors
        """
        today = date.today()
        pillar = self.calculate_day_pillar(today.year, today.month, today.day)
        element = STEM_ELEMENTS.get(pillar.heavenly, "earth")
        
        # 今日幸運色：與日干相生的五行顏色
        lucky_element = ELEMENT_GENERATE.get(element, "earth")
        
        colors = []
        for color in ELEMENT_COLORS.get(lucky_element, [])[:2]:
            colors.append({**color, "element": lucky_element})
        
        # 加入日干本身的顏色
        for color in ELEMENT_COLORS.get(element, [])[:1]:
            colors.append({**color, "element": element})
        
        return colors


# Singleton instance
destiny_service = DestinyService()

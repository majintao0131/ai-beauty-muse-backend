"""
Tests for Destiny Service - BaZi calculations
"""
import pytest
from app.services.destiny_service import DestinyService, ELEMENT_NAMES


@pytest.fixture
def destiny_service():
    """Create destiny service instance."""
    return DestinyService()


class TestBaziCalculations:
    """Test BaZi calculation functions."""
    
    def test_year_pillar_1984(self, destiny_service):
        """Test year pillar for 1984 (甲子年)."""
        pillar = destiny_service.calculate_year_pillar(1984)
        assert pillar.heavenly == "甲"
        assert pillar.earthly == "子"
    
    def test_year_pillar_2024(self, destiny_service):
        """Test year pillar for 2024 (甲辰年)."""
        pillar = destiny_service.calculate_year_pillar(2024)
        assert pillar.heavenly == "甲"
        assert pillar.earthly == "辰"
    
    def test_year_pillar_1990(self, destiny_service):
        """Test year pillar for 1990 (庚午年)."""
        pillar = destiny_service.calculate_year_pillar(1990)
        assert pillar.heavenly == "庚"
        assert pillar.earthly == "午"
    
    def test_day_pillar_calculation(self, destiny_service):
        """Test day pillar calculation."""
        # Test a known date
        pillar = destiny_service.calculate_day_pillar(2000, 1, 1)
        assert pillar.heavenly == "甲"
        assert pillar.earthly == "午"
    
    def test_bazi_complete(self, destiny_service):
        """Test complete BaZi calculation."""
        pillars = destiny_service.calculate_bazi(1990, 5, 15, 12)
        assert len(pillars) == 4
        # All pillars should have valid stems and branches
        for pillar in pillars:
            assert pillar.heavenly in "甲乙丙丁戊己庚辛壬癸?"
            assert pillar.earthly in "子丑寅卯辰巳午未申酉戌亥?"
    
    def test_bazi_without_hour(self, destiny_service):
        """Test BaZi calculation without birth hour."""
        pillars = destiny_service.calculate_bazi(1990, 5, 15)
        assert len(pillars) == 4
        # Last pillar should be unknown
        assert pillars[3].heavenly == "?"
        assert pillars[3].earthly == "?"


class TestFiveElements:
    """Test five elements calculations."""
    
    def test_count_five_elements(self, destiny_service):
        """Test five elements counting."""
        pillars = destiny_service.calculate_bazi(1990, 5, 15, 12)
        counts = destiny_service.count_five_elements(pillars)
        
        # Should have all five elements
        assert "wood" in counts
        assert "fire" in counts
        assert "earth" in counts
        assert "metal" in counts
        assert "water" in counts
        
        # Total should be 8 (4 stems + 4 branches)
        assert sum(counts.values()) == 8
    
    def test_day_master_analysis(self, destiny_service):
        """Test day master analysis."""
        pillars = destiny_service.calculate_bazi(1990, 5, 15, 12)
        day_master, analysis = destiny_service.analyze_day_master(pillars)
        
        assert day_master is not None
        assert analysis is not None
        assert len(analysis) > 0
    
    def test_favorable_element(self, destiny_service):
        """Test favorable element calculation."""
        pillars = destiny_service.calculate_bazi(1990, 5, 15, 12)
        favorable = destiny_service.get_favorable_element(pillars)
        
        # Should be one of the five elements in Chinese
        assert favorable in ELEMENT_NAMES.values()


class TestColorRecommendations:
    """Test color recommendation functions."""
    
    def test_color_recommendations(self, destiny_service):
        """Test color recommendations based on BaZi."""
        pillars = destiny_service.calculate_bazi(1990, 5, 15, 12)
        enhance, balance, avoid = destiny_service.get_color_recommendations(pillars)
        
        # Should have colors in each category
        assert len(enhance) > 0
        assert len(balance) > 0
        assert len(avoid) > 0
        
        # Each color should have name, hex, and element
        for color in enhance:
            assert "name" in color
            assert "hex" in color
            assert "element" in color


class TestDailyEnergy:
    """Test daily energy functions."""
    
    def test_today_stem_branch(self, destiny_service):
        """Test today's stem and branch."""
        stem_branch = destiny_service.get_today_stem_branch()
        
        assert len(stem_branch) == 2
        assert stem_branch[0] in "甲乙丙丁戊己庚辛壬癸"
        assert stem_branch[1] in "子丑寅卯辰巳午未申酉戌亥"
    
    def test_today_element(self, destiny_service):
        """Test today's element."""
        element = destiny_service.get_today_element()
        
        assert element in ELEMENT_NAMES.values()
    
    def test_today_lucky_colors(self, destiny_service):
        """Test today's lucky colors."""
        colors = destiny_service.get_today_lucky_colors()
        
        assert len(colors) > 0
        for color in colors:
            assert "name" in color
            assert "hex" in color


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

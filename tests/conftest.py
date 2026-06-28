"""Shared pytest fixtures for fuel-intel tests."""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def sample_location():
    return {
        "name": "Test Mumbai Metro",
        "lat": 19.076,
        "lng": 72.878,
        "state": "Maharashtra",
        "tier": "metro",
        "demand": 90,
        "competition": 35,
        "income": 88,
        "ev_readiness": 60,
        "infrastructure": 85,
        "growth_trajectory": 70,
    }


@pytest.fixture
def highway_location():
    return {
        "name": "Test Highway Hub",
        "lat": 18.75,
        "lng": 73.41,
        "state": "Maharashtra",
        "tier": "highway",
        "demand": 70,
        "competition": 25,
        "income": 60,
        "ev_readiness": 40,
        "infrastructure": 90,
        "growth_trajectory": 65,
    }


@pytest.fixture
def low_demand_tier3():
    return {
        "name": "Test Rural Tier3",
        "lat": 25.0,
        "lng": 85.0,
        "state": "Bihar",
        "tier": "tier3",
        "demand": 30,
        "competition": 60,
        "income": 35,
        "ev_readiness": 10,
        "infrastructure": 40,
        "growth_trajectory": 35,
    }


@pytest.fixture
def ev_metro_location():
    return {
        "name": "Test EV Metro",
        "lat": 12.935,
        "lng": 77.625,
        "state": "Karnataka",
        "tier": "metro",
        "demand": 85,
        "competition": 40,
        "income": 90,
        "ev_readiness": 80,
        "infrastructure": 82,
        "growth_trajectory": 78,
    }

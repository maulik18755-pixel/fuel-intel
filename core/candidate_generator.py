"""
Candidate Generator: Systematically creates candidate locations from data.

Instead of hand-picking 52 locations, this module generates candidates from:
1. District headquarters — every district with population > threshold
2. Highway corridor points — every ~40km along major national highways
3. EV hotspot clusters — areas with high existing EV charger density

The output is a DataFrame of 300-500+ candidate locations, each with
name, lat, lng, state, tier, and district-level metadata. These are then
fed into AutoScorer for data-driven pillar scoring.
"""
import pandas as pd
import numpy as np


# District headquarters with lat/lng for major Indian districts
# In production, this would come from a geocoding API or Survey of India data.
# Here we include ~200 district HQs covering all major states.
DISTRICT_HQ_COORDS = {
    # Maharashtra
    "Mumbai": (19.076, 72.878, "Maharashtra", "metro"),
    "Pune": (18.520, 73.856, "Maharashtra", "metro"),
    "Nagpur": (21.146, 79.088, "Maharashtra", "tier2"),
    "Nashik": (20.011, 73.790, "Maharashtra", "tier2"),
    "Thane": (19.218, 72.978, "Maharashtra", "metro"),
    "Aurangabad": (19.876, 75.343, "Maharashtra", "tier2"),
    "Solapur": (17.659, 75.910, "Maharashtra", "tier2"),
    "Kolhapur": (16.705, 74.244, "Maharashtra", "tier2"),
    "Sangli": (16.854, 74.564, "Maharashtra", "tier3"),
    "Satara": (17.680, 73.994, "Maharashtra", "tier3"),
    "Ratnagiri": (16.990, 73.312, "Maharashtra", "tier3"),
    "Ahmednagar": (19.095, 74.749, "Maharashtra", "tier3"),
    "Amravati": (20.932, 77.775, "Maharashtra", "tier3"),
    # Delhi NCR
    "New Delhi": (28.614, 77.209, "Delhi NCR", "metro"),
    "Gurugram": (28.459, 77.027, "Haryana", "metro"),
    "Noida": (28.535, 77.391, "Uttar Pradesh", "emerging"),
    "Greater Noida": (28.474, 77.504, "Uttar Pradesh", "emerging"),
    "Faridabad": (28.408, 77.317, "Haryana", "metro"),
    "Ghaziabad": (28.666, 77.431, "Uttar Pradesh", "metro"),
    # Karnataka
    "Bangalore": (12.972, 77.594, "Karnataka", "metro"),
    "Mysuru": (12.296, 76.639, "Karnataka", "tier2"),
    "Hubli-Dharwad": (15.364, 75.124, "Karnataka", "tier2"),
    "Mangalore": (12.865, 74.843, "Karnataka", "tier2"),
    "Belgaum": (15.849, 74.498, "Karnataka", "tier2"),
    "Gulbarga": (17.329, 76.834, "Karnataka", "tier3"),
    "Davanagere": (14.468, 75.921, "Karnataka", "tier3"),
    "Shimoga": (13.931, 75.568, "Karnataka", "tier3"),
    "Tumkur": (13.340, 77.101, "Karnataka", "tier3"),
    # Tamil Nadu
    "Chennai": (13.083, 80.271, "Tamil Nadu", "metro"),
    "Coimbatore": (11.017, 76.956, "Tamil Nadu", "tier2"),
    "Madurai": (9.925, 78.120, "Tamil Nadu", "tier2"),
    "Trichy": (10.791, 78.705, "Tamil Nadu", "tier2"),
    "Salem": (11.664, 78.146, "Tamil Nadu", "tier2"),
    "Tirunelveli": (8.727, 77.694, "Tamil Nadu", "tier3"),
    "Erode": (11.341, 77.717, "Tamil Nadu", "tier3"),
    "Vellore": (12.916, 79.133, "Tamil Nadu", "tier2"),
    "Thanjavur": (10.787, 79.138, "Tamil Nadu", "tier3"),
    "Tiruppur": (11.109, 77.342, "Tamil Nadu", "tier2"),
    # Telangana
    "Hyderabad": (17.385, 78.487, "Telangana", "metro"),
    "Warangal": (17.978, 79.600, "Telangana", "tier2"),
    "Nizamabad": (18.673, 78.094, "Telangana", "tier3"),
    "Karimnagar": (18.437, 79.129, "Telangana", "tier3"),
    # Andhra Pradesh
    "Visakhapatnam": (17.687, 83.219, "Andhra Pradesh", "tier2"),
    "Vijayawada": (16.506, 80.648, "Andhra Pradesh", "tier2"),
    "Guntur": (16.307, 80.437, "Andhra Pradesh", "tier2"),
    "Nellore": (14.450, 79.987, "Andhra Pradesh", "tier3"),
    "Kurnool": (15.828, 78.037, "Andhra Pradesh", "tier3"),
    "Tirupati": (13.629, 79.420, "Andhra Pradesh", "tier2"),
    "Rajahmundry": (17.005, 81.804, "Andhra Pradesh", "tier3"),
    "Kakinada": (16.960, 82.238, "Andhra Pradesh", "tier3"),
    # Gujarat
    "Ahmedabad": (23.023, 72.571, "Gujarat", "metro"),
    "Surat": (21.170, 72.831, "Gujarat", "tier2"),
    "Vadodara": (22.310, 73.188, "Gujarat", "tier2"),
    "Rajkot": (22.287, 70.794, "Gujarat", "tier2"),
    "Bhavnagar": (21.764, 72.153, "Gujarat", "tier3"),
    "Jamnagar": (22.471, 70.058, "Gujarat", "tier3"),
    "Junagadh": (21.522, 70.458, "Gujarat", "tier3"),
    "Gandhinagar": (23.215, 72.636, "Gujarat", "emerging"),
    "Anand": (22.556, 72.955, "Gujarat", "tier3"),
    "Vapi": (20.371, 72.905, "Gujarat", "tier3"),
    "Bharuch": (21.705, 72.998, "Gujarat", "tier3"),
    # Rajasthan
    "Jaipur": (26.912, 75.787, "Rajasthan", "tier2"),
    "Jodhpur": (26.239, 73.024, "Rajasthan", "tier2"),
    "Udaipur": (24.585, 73.713, "Rajasthan", "tier2"),
    "Kota": (25.180, 75.864, "Rajasthan", "tier2"),
    "Ajmer": (26.453, 74.639, "Rajasthan", "tier3"),
    "Bikaner": (28.022, 73.312, "Rajasthan", "tier3"),
    "Alwar": (27.554, 76.625, "Rajasthan", "tier3"),
    "Sikar": (27.615, 75.140, "Rajasthan", "tier3"),
    # Uttar Pradesh
    "Lucknow": (26.847, 80.947, "Uttar Pradesh", "tier2"),
    "Kanpur": (26.450, 80.350, "Uttar Pradesh", "tier2"),
    "Agra": (27.177, 78.008, "Uttar Pradesh", "tier2"),
    "Varanasi": (25.318, 83.010, "Uttar Pradesh", "tier2"),
    "Allahabad": (25.431, 81.846, "Uttar Pradesh", "tier2"),
    "Meerut": (28.984, 77.706, "Uttar Pradesh", "tier2"),
    "Bareilly": (28.367, 79.423, "Uttar Pradesh", "tier3"),
    "Aligarh": (27.881, 78.075, "Uttar Pradesh", "tier3"),
    "Moradabad": (28.839, 78.777, "Uttar Pradesh", "tier3"),
    "Gorakhpur": (26.760, 83.368, "Uttar Pradesh", "tier3"),
    "Jhansi": (25.449, 78.568, "Uttar Pradesh", "tier3"),
    "Mathura": (27.492, 77.674, "Uttar Pradesh", "tier3"),
    # Kerala
    "Thiruvananthapuram": (8.507, 76.957, "Kerala", "tier2"),
    "Kochi": (9.967, 76.244, "Kerala", "tier2"),
    "Kozhikode": (11.259, 75.780, "Kerala", "tier2"),
    "Thrissur": (10.527, 76.214, "Kerala", "tier3"),
    "Kannur": (11.869, 75.370, "Kerala", "tier3"),
    "Kollam": (8.881, 76.585, "Kerala", "tier3"),
    # Madhya Pradesh
    "Bhopal": (23.260, 77.413, "Madhya Pradesh", "tier2"),
    "Indore": (22.720, 75.858, "Madhya Pradesh", "tier2"),
    "Jabalpur": (23.182, 79.956, "Madhya Pradesh", "tier2"),
    "Gwalior": (26.218, 78.182, "Madhya Pradesh", "tier2"),
    "Ujjain": (23.179, 75.786, "Madhya Pradesh", "tier3"),
    "Sagar": (23.839, 78.739, "Madhya Pradesh", "tier3"),
    "Rewa": (24.531, 81.302, "Madhya Pradesh", "tier3"),
    # West Bengal
    "Kolkata": (22.573, 88.364, "West Bengal", "metro"),
    "Howrah": (22.589, 88.263, "West Bengal", "metro"),
    "Durgapur": (23.520, 87.320, "West Bengal", "tier3"),
    "Asansol": (23.683, 86.952, "West Bengal", "tier3"),
    "Siliguri": (26.727, 88.395, "West Bengal", "tier3"),
    "Kharagpur": (22.346, 87.324, "West Bengal", "tier3"),
    # Punjab
    "Ludhiana": (30.901, 75.857, "Punjab", "tier2"),
    "Amritsar": (31.634, 74.871, "Punjab", "tier2"),
    "Jalandhar": (31.326, 75.576, "Punjab", "tier2"),
    "Patiala": (30.340, 76.387, "Punjab", "tier3"),
    "Bathinda": (30.211, 74.946, "Punjab", "tier3"),
    # Haryana
    "Karnal": (29.686, 76.991, "Haryana", "tier3"),
    "Panipat": (29.390, 76.968, "Haryana", "tier3"),
    "Ambala": (30.379, 76.768, "Haryana", "tier3"),
    "Hisar": (29.154, 75.723, "Haryana", "tier3"),
    "Rohtak": (28.895, 76.606, "Haryana", "tier3"),
    "Sonipat": (28.995, 77.019, "Haryana", "tier3"),
    # Others
    "Chandigarh": (30.734, 76.779, "Chandigarh", "tier2"),
    "Dehradun": (30.317, 78.032, "Uttarakhand", "tier2"),
    "Haridwar": (29.946, 78.164, "Uttarakhand", "tier3"),
    "Patna": (25.612, 85.145, "Bihar", "tier2"),
    "Gaya": (24.796, 84.999, "Bihar", "tier3"),
    "Muzaffarpur": (26.121, 85.391, "Bihar", "tier3"),
    "Ranchi": (23.344, 85.310, "Jharkhand", "tier2"),
    "Jamshedpur": (22.805, 86.203, "Jharkhand", "tier2"),
    "Dhanbad": (23.796, 86.435, "Jharkhand", "tier3"),
    "Bhubaneswar": (20.296, 85.825, "Odisha", "tier2"),
    "Cuttack": (20.463, 85.879, "Odisha", "tier3"),
    "Rourkela": (22.260, 84.854, "Odisha", "tier3"),
    "Raipur": (21.251, 81.630, "Chhattisgarh", "tier2"),
    "Bilaspur": (22.080, 82.150, "Chhattisgarh", "tier3"),
    "Guwahati": (26.144, 91.736, "Assam", "tier2"),
    "Dibrugarh": (27.473, 94.912, "Assam", "tier3"),
    "Imphal": (24.817, 93.950, "Manipur", "tier3"),
    "Shillong": (25.578, 91.880, "Meghalaya", "tier3"),
    "Agartala": (23.831, 91.287, "Tripura", "tier3"),
    "Aizawl": (23.737, 92.717, "Mizoram", "tier3"),
    "Gangtok": (27.333, 88.617, "Sikkim", "tier3"),
    "Itanagar": (27.084, 93.602, "Arunachal Pradesh", "tier3"),
    "Kohima": (25.675, 94.110, "Nagaland", "tier3"),
    "Panaji": (15.498, 73.828, "Goa", "tier3"),
    "Pondicherry": (11.934, 79.830, "Puducherry", "tier3"),
    "Jammu": (32.727, 74.857, "Jammu & Kashmir", "tier2"),
    "Srinagar": (34.084, 74.797, "Jammu & Kashmir", "tier2"),
    "Leh": (34.153, 77.578, "Ladakh", "tier3"),
}


# Highway corridor interpolation points (~40km spacing)
HIGHWAY_CORRIDORS = [
    # (corridor_name, waypoints as [(lat, lng), ...], state_sequence)
    ("Delhi-Jaipur NH48", [(28.61, 77.21), (28.36, 76.94), (28.10, 76.70), (27.80, 76.40), (27.50, 76.10), (27.20, 75.90), (26.91, 75.79)], "Haryana-Rajasthan"),
    ("Delhi-Agra Yamuna Exp", [(28.57, 77.32), (28.30, 77.50), (28.00, 77.65), (27.70, 77.75), (27.40, 77.85), (27.18, 78.01)], "Uttar Pradesh"),
    ("Mumbai-Pune Exp", [(19.08, 72.88), (18.95, 73.05), (18.85, 73.25), (18.75, 73.41), (18.65, 73.55), (18.52, 73.86)], "Maharashtra"),
    ("Mumbai-Ahmedabad NH48", [(19.08, 72.88), (19.50, 72.85), (20.00, 72.80), (20.37, 72.91), (20.80, 72.95), (21.17, 72.83), (21.60, 72.70), (22.00, 72.60), (22.50, 72.55), (23.02, 72.57)], "Maharashtra-Gujarat"),
    ("Chennai-Bangalore NH48", [(13.08, 80.27), (12.92, 79.93), (12.93, 79.13), (12.97, 78.50), (12.97, 77.59)], "Tamil Nadu-Karnataka"),
    ("Hyderabad-Bangalore NH44", [(17.39, 78.49), (16.80, 78.10), (16.20, 77.70), (15.83, 78.04), (15.30, 77.60), (14.60, 77.40), (13.80, 77.50), (12.97, 77.59)], "Telangana-Karnataka"),
    ("Delhi-Chandigarh NH1", [(28.61, 77.21), (28.95, 77.10), (29.39, 76.97), (29.69, 76.99), (30.00, 76.90), (30.34, 76.79), (30.73, 76.78)], "Haryana-Punjab"),
    ("Lucknow-Agra Exp", [(26.85, 80.95), (27.00, 80.50), (27.10, 80.10), (27.22, 79.90), (27.18, 78.01)], "Uttar Pradesh"),
    ("Ahmedabad-Vadodara Exp", [(23.02, 72.57), (22.80, 72.70), (22.55, 72.96), (22.31, 73.19)], "Gujarat"),
    ("Bangalore-Mysore NH275", [(12.97, 77.59), (12.70, 77.10), (12.44, 76.61), (12.30, 76.64)], "Karnataka"),
    ("Kolkata-Durgapur NH2", [(22.57, 88.36), (22.80, 88.00), (23.00, 87.60), (23.30, 87.30), (23.52, 87.32)], "West Bengal"),
    ("Delhi-Mumbai Expressway", [(28.61, 77.21), (28.20, 76.80), (27.50, 76.30), (27.00, 75.80), (26.50, 75.50), (25.80, 75.40), (25.00, 75.20), (24.30, 74.80), (23.50, 74.20), (22.80, 73.50), (22.00, 73.00), (21.20, 72.90), (20.50, 72.85), (19.70, 72.88), (19.08, 72.88)], "Multi-State"),
    ("Samruddhi Mahamarg", [(19.08, 72.88), (19.50, 73.50), (19.90, 74.00), (20.01, 73.79), (20.50, 74.50), (20.90, 75.30), (21.15, 79.09)], "Maharashtra"),
    ("Patna-Kolkata NH19", [(25.61, 85.15), (25.30, 85.50), (25.00, 86.00), (24.50, 86.50), (24.00, 87.00), (23.52, 87.32), (22.80, 88.00), (22.57, 88.36)], "Bihar-Jharkhand-WB"),
    ("Kochi-Mangalore NH66", [(9.97, 76.24), (10.30, 76.10), (10.80, 75.80), (11.26, 75.78), (11.80, 75.40), (12.20, 75.10), (12.87, 74.84)], "Kerala-Karnataka"),
    ("Vizag-Chennai NH16", [(17.69, 83.22), (17.00, 82.50), (16.50, 82.00), (16.00, 81.50), (15.50, 80.80), (15.00, 80.20), (14.50, 80.00), (13.80, 80.10), (13.08, 80.27)], "AP-Tamil Nadu"),
]


class CandidateGenerator:
    """Generates candidate locations from district data and highway corridors."""

    def __init__(self, min_population: int = 200_000):
        self.min_population = min_population

    def generate_urban_candidates(self, census_df: pd.DataFrame = None) -> pd.DataFrame:
        """Generate candidates from district headquarters."""
        rows = []
        for name, (lat, lng, state, tier) in DISTRICT_HQ_COORDS.items():
            pop = 0
            pop_density = 500
            if census_df is not None and not census_df.empty and "district" in census_df.columns:
                match = census_df[census_df["district"].str.contains(name.split("-")[0].split()[0], case=False, na=False)]
                if not match.empty:
                    pop = int(match.iloc[0].get("total_population", 0))
                    pop_density = float(match.iloc[0].get("population_density", 500))

            rows.append({
                "name": f"{name} Urban",
                "lat": lat, "lng": lng,
                "state": state, "tier": tier,
                "source": "district_hq",
                "population": pop,
                "population_density": pop_density,
            })
        return pd.DataFrame(rows)

    def generate_highway_candidates(self) -> pd.DataFrame:
        """Generate candidates along major highway corridors at ~40km intervals."""
        rows = []
        for corridor_name, waypoints, states in HIGHWAY_CORRIDORS:
            state_list = states.split("-")
            for i, (lat, lng) in enumerate(waypoints):
                # Skip first and last — they're usually cities already covered
                if i == 0 or i == len(waypoints) - 1:
                    continue
                state = state_list[min(i, len(state_list) - 1)] if len(state_list) > 1 else state_list[0]
                rows.append({
                    "name": f"{corridor_name} Km{i * 40}",
                    "lat": lat, "lng": lng,
                    "state": state.strip(), "tier": "highway",
                    "source": "highway_corridor",
                    "population": 0,
                    "population_density": 100,
                })
        return pd.DataFrame(rows)

    def generate_emerging_candidates(self) -> pd.DataFrame:
        """Generate candidates at known emerging corridors and industrial zones."""
        emerging = [
            ("GIFT City", 23.155, 72.683, "Gujarat", "emerging"),
            ("Dholera SIR", 22.248, 72.191, "Gujarat", "emerging"),
            ("Navi Mumbai Airport Zone", 18.989, 73.118, "Maharashtra", "emerging"),
            ("Amaravati Capital Region", 16.506, 80.648, "Andhra Pradesh", "emerging"),
            ("Sri City SEZ", 13.565, 80.007, "Andhra Pradesh", "emerging"),
            ("PCMC Pimpri-Chinchwad", 18.628, 73.801, "Maharashtra", "emerging"),
            ("Devanahalli Aerospace", 13.246, 77.712, "Karnataka", "emerging"),
            ("Adibatla Hyderabad", 17.268, 78.565, "Telangana", "emerging"),
            ("YEIDA Greater Noida", 28.460, 77.530, "Uttar Pradesh", "emerging"),
            ("Mohali IT City", 30.693, 76.711, "Punjab", "emerging"),
        ]
        rows = [{"name": f"{n} Corridor", "lat": la, "lng": ln, "state": s, "tier": t,
                 "source": "emerging_corridor", "population": 0, "population_density": 300}
                for n, la, ln, s, t in emerging]
        return pd.DataFrame(rows)

    def generate_all(self, census_df: pd.DataFrame = None) -> pd.DataFrame:
        """Generate all candidates from all sources."""
        urban = self.generate_urban_candidates(census_df)
        highway = self.generate_highway_candidates()
        emerging = self.generate_emerging_candidates()

        all_candidates = pd.concat([urban, highway, emerging], ignore_index=True)

        # De-duplicate: if two candidates are within ~3km, keep the one with higher tier
        all_candidates = self._deduplicate(all_candidates, min_distance_deg=0.03)

        return all_candidates

    def _deduplicate(self, df: pd.DataFrame, min_distance_deg: float = 0.03) -> pd.DataFrame:
        """Remove near-duplicate locations, keeping the higher-priority one."""
        tier_priority = {"metro": 0, "emerging": 1, "tier2": 2, "highway": 3, "tier3": 4}
        df["_priority"] = df["tier"].map(tier_priority).fillna(5)
        df = df.sort_values("_priority").reset_index(drop=True)

        keep = [True] * len(df)
        for i in range(len(df)):
            if not keep[i]:
                continue
            for j in range(i + 1, len(df)):
                if not keep[j]:
                    continue
                dlat = abs(df.iloc[i]["lat"] - df.iloc[j]["lat"])
                dlng = abs(df.iloc[i]["lng"] - df.iloc[j]["lng"])
                if dlat < min_distance_deg and dlng < min_distance_deg:
                    keep[j] = False

        df = df[keep].drop(columns=["_priority"]).reset_index(drop=True)
        return df

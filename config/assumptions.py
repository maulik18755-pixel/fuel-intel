"""
Documented model assumptions for full transparency.
Each assumption is traceable, categorized, and rated for sensitivity.
Displayed in the Architecture & Data tab.
"""

MODEL_ASSUMPTIONS = [
    # --- Financial (8) ---
    {"id": "A001", "category": "Financial", "assumption": "Discount rate for NPV calculation set at 12%, reflecting India's weighted average cost of capital for infrastructure projects", "value": "12%", "source": "CRISIL Infrastructure Yearbook 2024", "sensitivity": "High"},
    {"id": "A002", "category": "Financial", "assumption": "Fuel retail margin per litre based on PPAC published dealer margin data for FY2024", "value": "₹3.50/litre", "source": "PPAC Dealer Margin Report FY2024", "sensitivity": "High"},
    {"id": "A003", "category": "Financial", "assumption": "EV charging margin per kWh based on CERC tariff guidelines and DC fast charging operator benchmarks", "value": "₹10.00/kWh", "source": "CERC Tariff Order 2023 + Tata Power/ChargeZone Data", "sensitivity": "High"},
    {"id": "A004", "category": "Financial", "assumption": "Financial projections over 15-year horizon matching typical fuel retail BOT concession periods in India", "value": "15 years", "source": "NHAI BOT Concession Framework", "sensitivity": "Medium"},
    {"id": "A005", "category": "Financial", "assumption": "Convenience store revenue per sqft benchmarked against organized retail averages in fuel station format", "value": "₹1,200/sqft/year", "source": "Reliance Retail Industry Benchmark", "sensitivity": "Medium"},
    {"id": "A006", "category": "Financial", "assumption": "Annual operating expenses as percentage of initial CAPEX, industry standard for fuel retail operations", "value": "3.5% of CAPEX", "source": "IOCL Annual Report FY2024", "sensitivity": "Low"},
    {"id": "A007", "category": "Financial", "assumption": "EV charger equipment replacement at 20% of charger CAPEX in year 8 based on equipment lifecycle", "value": "20% in Year 8", "source": "ABB / Delta Electronics Equipment Warranty Data", "sensitivity": "Medium"},
    {"id": "A008", "category": "Financial", "assumption": "Convenience retail revenue grows at 5% annually, in line with consumer price inflation and footfall growth", "value": "5% annual growth", "source": "RBI CPI Trend Analysis", "sensitivity": "Low"},

    # --- Market (7) ---
    {"id": "A009", "category": "Market", "assumption": "Fuel volume declines 2% annually starting from year 5 as EV adoption accelerates", "value": "2% annual decline from Y5", "source": "IEA India Energy Outlook 2023", "sensitivity": "High"},
    {"id": "A010", "category": "Market", "assumption": "EV adoption follows logistic S-curve with 15% annual growth from current installed base", "value": "15% annual growth", "source": "NITI Aayog EV Mission Report + SMEV Data", "sensitivity": "High"},
    {"id": "A011", "category": "Market", "assumption": "Daily vehicle throughput estimated from demand score: maximum 800 vehicles/day at score 100, scaling linearly", "value": "800 vehicles/day at 100", "source": "IOCL Average Throughput Data", "sensitivity": "Medium"},
    {"id": "A012", "category": "Market", "assumption": "Average fuel fill volume per stop: 25 litres for passenger cars, 80 litres for commercial vehicles", "value": "25L car / 80L commercial", "source": "Industry Standard Estimates", "sensitivity": "Low"},
    {"id": "A013", "category": "Market", "assumption": "Vehicle mix varies by location tier — metros have higher car share, highways have higher commercial share", "value": "Metro 70:30 / Highway 40:60", "source": "Vahan Dashboard Registration Mix", "sensitivity": "Medium"},
    {"id": "A014", "category": "Market", "assumption": "EV charging sessions per charger per day start at 4 in year 1 and grow to 12 by year 10 on an S-curve", "value": "4 → 12 sessions/charger/day", "source": "Tata Power EZ Charge Utilization Data", "sensitivity": "Medium"},
    {"id": "A015", "category": "Market", "assumption": "Average energy delivered per EV charging session: 30 kWh (typical DC fast charge from 20% to 80% SoC)", "value": "30 kWh/session", "source": "ChargeZone Operating Data", "sensitivity": "Low"},

    # --- Infrastructure (5) ---
    {"id": "A016", "category": "Infrastructure", "assumption": "CAPEX estimates by format based on IOCL/BPCL annual reports and industry consultation for greenfield stations", "value": "₹8-22 Cr by format", "source": "IOCL/BPCL Annual Reports + Industry", "sensitivity": "Medium"},
    {"id": "A017", "category": "Infrastructure", "assumption": "Land lease rates sourced from state circle rates adjusted for commercial use along highways and urban corridors", "value": "₹8-35 L/year by tier", "source": "State Circle Rate Notifications", "sensitivity": "Medium"},
    {"id": "A018", "category": "Infrastructure", "assumption": "Electrical grid reliability assumed adequate for EV charging in metro and tier-2 cities; tier-3 may need backup", "value": "Adequate in metros/tier-2", "source": "CEA Grid Reliability Report 2024", "sensitivity": "Medium"},
    {"id": "A019", "category": "Infrastructure", "assumption": "Highway locations assume NHAI Right-of-Way availability for fuel station licensing under wayside amenity policy", "value": "ROW available", "source": "NHAI Wayside Amenity Policy 2023", "sensitivity": "Low"},
    {"id": "A020", "category": "Infrastructure", "assumption": "Smart City locations assume planned infrastructure improvements are delivered on the published schedule", "value": "On-schedule delivery", "source": "Smart Cities Mission Dashboard", "sensitivity": "Medium"},

    # --- Regulatory (4) ---
    {"id": "A021", "category": "Regulatory", "assumption": "No new fuel retail licensing restrictions introduced over the 15-year planning horizon", "value": "No new restrictions", "source": "MoPNG Policy Review", "sensitivity": "Medium"},
    {"id": "A022", "category": "Regulatory", "assumption": "State EV policies including purchase subsidies and charging mandates continue at current trajectory", "value": "Current trajectory", "source": "State EV Policy Compendium (NITI Aayog)", "sensitivity": "Medium"},
    {"id": "A023", "category": "Regulatory", "assumption": "GST on petroleum products assumed to remain outside GST framework for the projection period", "value": "Outside GST", "source": "GST Council Deliberations 2024", "sensitivity": "Low"},
    {"id": "A024", "category": "Regulatory", "assumption": "Carbon credit mechanisms and green hydrogen blending mandates not included in revenue projections (conservative)", "value": "Not modelled", "source": "Conservative Assumption", "sensitivity": "Low"},

    # --- Technology (4) ---
    {"id": "A025", "category": "Technology", "assumption": "DC fast chargers at 60-120kW as baseline, with 350kW ultra-fast as premium option for highway hubs", "value": "60-350kW range", "source": "CCS2 / CHAdeMO Standards", "sensitivity": "Medium"},
    {"id": "A026", "category": "Technology", "assumption": "Battery swap technology not included in base case due to standardization uncertainty across OEMs", "value": "Excluded", "source": "Industry Assessment", "sensitivity": "Low"},
    {"id": "A027", "category": "Technology", "assumption": "Autonomous vehicle impact on fuel demand not modelled within 15-year horizon", "value": "Not modelled", "source": "Conservative Assumption", "sensitivity": "Low"},
    {"id": "A028", "category": "Technology", "assumption": "Vehicle-to-Grid revenue potential excluded from projections pending regulatory framework development", "value": "Excluded", "source": "CEA V2G Working Group", "sensitivity": "Low"},
]

ASSUMPTION_CATEGORIES = ["Financial", "Market", "Infrastructure", "Regulatory", "Technology"]

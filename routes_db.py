# routes_db.py
# 升級版：N 對 N 任意導航地點庫 (Locations Database)

LOCATIONS = {
    "磐石": {
        "name": "磐石高中", "keywords": ["磐石"], 
        "lat": 24.8080, "lon": 120.9545, 
        "default_bus": "藍15區", "default_stop": "磐石"
    },
    "火車站": {
        "name": "新竹火車站", "keywords": ["火車", "車站"], 
        "lat": 24.8015, "lon": 120.9715, 
        "default_bus": "藍線", "default_stop": "火車站"
    },
    "巨城": {
        "name": "巨城購物中心", "keywords": ["巨城", "big city"], 
        "lat": 24.8105, "lon": 120.9752, 
        "default_bus": "51", "default_stop": "巨城"
    },
    "成德": {
        "name": "成德高中", "keywords": ["成德"], 
        "lat": 24.7935, "lon": 120.9385, 
        "default_bus": "83", "default_stop": "成德"
    },
    "城隍廟": {
        "name": "新竹都城隍廟", "keywords": ["城隍"], 
        "lat": 24.8045, "lon": 120.9655, 
        "default_bus": "藍15區", "default_stop": "城隍廟"
    },
    "清華": {
        "name": "國立清華大學", "keywords": ["清華", "清大", "清交"], 
        "lat": 24.7965, "lon": 120.9965, 
        "default_bus": "藍線", "default_stop": "清華"
    },
    "南寮": {
        "name": "南寮漁港", "keywords": ["南寮", "漁港"], 
        "lat": 24.8495, "lon": 120.9285, 
        "default_bus": "藍15區", "default_stop": "南寮"
    }
}
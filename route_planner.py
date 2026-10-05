import json

def find_bus_routes(destination: str, current_gps: dict) -> dict:
    """模組三：模擬交通 API 路線規劃核心邏輯"""
    
    # 模擬後端的公車路網資料庫（實際開發時可替換為 TDX 交通 API 請求）
    mock_routes_db = {
        "新竹火車站": [
            {
                "option_id": 1,
                "bus_route_name": "藍15區",
                "boarding_stop": "磐石高中",
                "alighting_stop": "新竹火車站",
                "estimated_wait_time_mins": 5,
                "travel_time_mins": 15,
                "fare": 15
            },
            {
                "option_id": 2,
                "bus_route_name": "23路",
                "boarding_stop": "中正市場",
                "alighting_stop": "火車站",
                "estimated_wait_time_mins": 8,
                "travel_time_mins": 18,
                "fare": 15
            }
        ],
        "巨城購物中心": [
            {
                "option_id": 1,
                "bus_route_name": "51路",
                "boarding_stop": "磐石高中",
                "alighting_stop": "巨城購物中心",
                "estimated_wait_time_mins": 6,
                "travel_time_mins": 12,
                "fare": 15
            }
        ]
    }

    # 根據目的地尋找對應的公車路線
    routes = mock_routes_db.get(destination, [])
    
    if routes:
        return {
            "status": "success",
            "destination": destination,
            "route_options": routes
        }
    else:
        return {
            "status": "not_found",
            "destination": destination,
            "message": "目前位置附近查無直達公車路線"
        }

if __name__ == "__main__":
    # 模擬從模組二萃取出來的目的地與用戶位置
    target_destination = "新竹火車站"
    user_gps = {"lat": 24.8080, "lng": 120.9545}

    print(f"=== 模組三：查詢前往 '{target_destination}' 的公車路線 ===")
    result = find_bus_routes(target_destination, user_gps)
    
    # 輸出符合規劃書格式的 JSON 結果
    print(json.dumps(result, ensure_ascii=False, indent=2))
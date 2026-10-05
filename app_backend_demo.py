import json

def extract_destination(user_input: str) -> str:
    """模組二：模擬 AI 意圖與目的地萃取"""
    if "新竹火車站" in user_input:
        return "新竹火車站"
    elif "磐石高中" in user_input:
        return "磐石高中"
    elif "巨城購物中心" in user_input:
        return "巨城購物中心"
    else:
        return "未知地點"

def find_bus_routes(destination: str) -> dict:
    """模組三：模擬交通 API 路線規劃"""
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

    routes = mock_routes_db.get(destination, [])
    if routes:
        return {"status": "success", "route_options": routes}
    else:
        return {"status": "not_found", "message": "查無直達公車路線"}

def process_user_request(user_input: str) -> str:
    """結合模組二與模組三的主處理流程"""
    print(f"\n[前端送出] 使用者輸入: 「{user_input}」")
    
    # 1. 透過模組二抓取目的地
    destination = extract_destination(user_input)
    print(f"[後端 AI 解析] 萃取出的目的地: {destination}")
    
    # 2. 透過模組三查詢路線
    route_result = find_bus_routes(destination)
    
    # 3. 打包成最終回應給前端 APP 的 JSON
    response_data = {
        "user_input": user_input,
        "extracted_destination": destination,
        "routing_result": route_result
    }
    
    return json.dumps(response_data, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    print("=== 智慧公車 APP 後端閉環模擬測試 ===")
    
    # 模擬使用者實際操作
    print(process_user_request("我現在要去新竹火車站"))
    print(process_user_request("請問怎麼搭車去巨城購物中心？"))
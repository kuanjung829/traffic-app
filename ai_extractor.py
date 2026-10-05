import json

def extract_intent_and_destination(user_input: str) -> dict:
    """本地模擬 AI 意圖與目的地萃取（不需 API Key 與網路額度）"""
    destination = None
    
    # 簡單的關鍵字對應邏輯來模擬 AI 解析
    if "新竹火車站" in user_input:
        destination = "新竹火車站"
    elif "磐石高中" in user_input:
        destination = "磐石高中"
    elif "巨城購物中心" in user_input:
        destination = "巨城購物中心"
    else:
        destination = "未知地點"

    return {
        "intent": "find_route",
        "destination": destination
    }

if __name__ == "__main__":
    test_sentences = [
        "我現在要去新竹火車站",
        "幫我導航到磐石高中",
        "請問怎麼搭車去巨城購物中心？",
    ]

    print("=== 本地模擬 AI 萃取測試 ===")
    for sentence in test_sentences:
        print(f"\n使用者輸入: {sentence}")
        output = extract_intent_and_destination(sentence)
        print("模擬萃取結果 (JSON):")
        print(json.dumps(output, ensure_ascii=False, indent=2))
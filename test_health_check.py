"""
헬스체크 API 테스트 스크립트
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_health_check():
    """헬스체크 API 테스트"""
    print("=" * 60)
    print("🏥 헬스체크 API 테스트")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE}/generate/health")
        
        print(f"\n📊 HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 전체 상태: {data['status'].upper()}")
            print(f"⏰ 타임스탬프: {data['timestamp']}")
            print("\n📋 상세 체크:")
            
            for check_name, check_data in data.get('checks', {}).items():
                status = check_data.get('status', 'unknown')
                message = check_data.get('message', '')
                
                if status == 'ok':
                    emoji = '✅'
                elif status == 'warning':
                    emoji = '⚠️'
                elif status == 'not_loaded':
                    emoji = '💤'
                else:
                    emoji = '❌'
                
                print(f"\n  {emoji} {check_name.upper()}:")
                print(f"     상태: {status}")
                print(f"     메시지: {message}")
                
                # 추가 정보 출력
                for key, value in check_data.items():
                    if key not in ['status', 'message']:
                        print(f"     {key}: {value}")
        
        elif response.status_code == 503:
            print("❌ 서비스 사용 불가 (Unhealthy)")
            print("\n상세 정보:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        else:
            print(f"⚠️ 예상치 못한 응답: {response.status_code}")
            print(response.text)
    
    except requests.exceptions.ConnectionError:
        print("❌ 서버 연결 실패")
        print("FastAPI 서버가 실행 중인지 확인하세요:")
        print("  uvicorn main:app --reload --port 8000")
    
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
    
    print("\n" + "=" * 60)


def test_deprecated_api():
    """Deprecated API 테스트 (삭제되었는지 확인)"""
    print("\n🗑️ Deprecated API 확인")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{API_BASE}/generate/music-v3",
            files={"file": ("test.txt", b"test content")},
            data={"book_id": "test", "page": 1}
        )
        
        if response.status_code == 404:
            print("✅ /music-v3 엔드포인트가 정상적으로 제거되었습니다")
        else:
            print(f"⚠️ 예상치 못한 응답: {response.status_code}")
            print(response.json())
    
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")


if __name__ == "__main__":
    test_health_check()
    test_deprecated_api()


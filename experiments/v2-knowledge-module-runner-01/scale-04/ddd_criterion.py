"""Frozen DDD2 prompt protocol; no private calibration evidence is distributed."""
import hashlib

DDD2_HEAD = (
 "용어: 도메인 = 업무 영역. 주어 = 그 도메인 안에서 사실들이 모이는 대상 이름. candidates[{i}] 의 name 을 "
 "area 도메인의 주어로 쓰는 것이 적합한가? example 문장은 이 이름이 쓰인 예시다. "
)
DDD_BODY = (
 "기준(DDD): 도메인은 경계 컨텍스트다. 주어는 그 안의 엔티티, 즉 상태가 바뀌어도 같은 대상으로 계속 추적되는 대상(또는 여러 대상을 묶는 대표)이다. "
 "주어 맞음: 화면·모달·컴포넌트, API, 데이터/테이블, 이름 붙은 서비스·도구·환경, 상태를 가진 업무 대상. "
 "주어 아님(그것을 가진 대표가 주어다): 정책·규칙·기준·규율, 동작·처리·조정·생성·수정·배포(rollout)·흐름 같은 과정, "
 "역할·상태·값·권한 속성, 테스트·회귀 보호·감사·기록·전략 문서, 대상의 한 기능·설정, 화면의 부분·레이아웃·스크롤·색상. "
 "예시: '결제 확인 모달' 맞음, 'order.create API' 맞음, '주문' 맞음, '반품 신청' 맞음, 'Sentry' 맞음 / "
 "'주문 취소 정책'→주문, '배송 출고 처리'→배송, 'Sentry 알림 조정'→Sentry, '담당 매니저'→주문의 역할, "
 "'결제 회귀 테스트'→결제, '장바구니 쿠폰 적용'→장바구니, '확인 버튼'→모달 은 모두 주어 아님.")
DDD2 = DDD2_HEAD + DDD_BODY  # Jev question; bytes identical to calibrated text
DDD_TERMS = "용어: 도메인 = 업무 영역(경계 컨텍스트). 주어 = 그 도메인 안에서 사실들이 모이는 대상 이름. "
DDD_FOR_AUTHOR = DDD_TERMS + DDD_BODY  # Luna tasks: criterion only, no Jev question or {i} placeholder
CALIBRATED_SHA256 = '64bd00b94c76d06fbbca80c581ccdc8db57eb95f66efca43079e14b80a42931d'

DOMAIN_CRITERION = (
    '정의: 도메인은 여러 주어를 담는 업무 영역(DDD 경계 컨텍스트)이다. 같은 업무 능력과 용어의 경계를 기준으로 한다. '
    '화면·모달·컴포넌트·API·도구·파일은 주어이며 절대로 도메인이 아니다. 정책/동작/부분의 이름도 도메인이 아니다. '
    '기능이나 화면이 달라도 같은 업무 영역이면 같은 도메인이다. 관련 있다는 이유만으로 다른 업무 영역을 같다고 하지 않는다. '
    '고정 예시(시험 문서와 무관): 물류=도메인, 재고=도메인, 인사=도메인; '
    '배송 확인 모달·StockGrid 컴포넌트·parcel.create API·ParcelProbe 도구·stock.py 파일=주어, 도메인 아님. '
    '배송 확인 모달과 출고 전표는 물류 안의 서로 다른 주어지만 같은 도메인이다. ')
DOMAIN_QUESTION = DOMAIN_CRITERION + 'candidate의 name/description은 업무 영역 이름으로 적합한가? 예/아니오 확률로 답한다.'
DOMAIN_SAME_QUESTION = DOMAIN_CRITERION + ('candidate와 proposed가 같은 업무 영역을 가리키는가? '
    '이름·설명·unit 전체를 비교한다. 같으면 기존 영역을 재사용한다. 예/아니오 확률로 답한다.')

def criterion_sha():
    return hashlib.sha256(DDD2.encode()).hexdigest()

def assert_calibrated():
    if criterion_sha() != CALIBRATED_SHA256:
        raise ValueError('DDD2 criterion drift: recalibrate and obtain approval before updating the frozen hash')

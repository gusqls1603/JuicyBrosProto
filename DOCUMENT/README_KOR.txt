§ 클라이언트 실행 방법 §
python3 client.py [groupID]		EX. python3 client.py testgroup01

§ groupID 생성 방법 §
python3 FaceAPI.py 입력 후 안내에 따라 진행
생성된 group은 MS 서버에 저장되며, 구독 키 1개로 1000개의 group 생성 가능
여기서 말하는 group을 LargePersonGroup 이라 칭함

§ cfg_var.py §
사용자 환경에 따라 변경될 수 있는 변수 (디렉토리, 가게 위치 등) 설정 가능
cfg_var.py 에서 정의한 변수는 cfg_ 로 시작하게 하여 구별 가능

§ msg_var.py §
외국인 고객을 상정하고 만들었으나, 한글/영어를 전환하는 기능이 구현되지 않았음
cfg_var.py와 마찬가지로 변수명이 msg_ 로 시작

ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ

§ 회원가입 및 로그인 시 API 호출 순서 §
1. 일단 카메라를 통해 고객의 사진을 찍고 나면, 해당 사진이 Detect API를 통해 MS 서버에 전송되고, 감지된 얼굴의 정보와 그 정보의 식별ID를 반환한다. 이 ID를 faceID 라고 부르며, 24시간 경과 후 MS 서버에서 삭제된다.

2-1-1. 고객이 회원가입을 시도할 경우, 먼저 Create_personid API가 호출되어 고객이 입력한 닉네임으로부터 고유의 personID를 생성한다.
2-1-2. group 내에서 고객을 구별할 personID를 만들었으니, Addface API가 호출되어 group 내에 고객 정보를 personID 및 얼굴 정보와 함께 저장하며, 이 정보의 식별 ID를 반환한다. 이 ID는 persistedfaceid 라고 부르며 해당 정보를 삭제하는 API가 호출되지 않는 한 MS 서버에 영구적으로 보관된다. (해당 삭제 API 호출 코드는 구현하지 않음)
2-1-3. group 내에 고객 정보를 추가한 뒤엔, Train API가 호출된다. group의 train이 진행되지 않으면 로그인 시 호출할 Identify API를 호출할 수 없다
cf. 흐름도.pdf

2-2-1. 고객이 로그인을 시도할 경우, Identify API가 호출되어 1번에서 확보한 얼굴정보와 매칭되는 얼굴을 group 내에서 찾은 뒤, 가장 높은 수치로 매칭되는 사람의 personID를 반환한다.

+@. FaceAPI.py에 별도로 구현되어 있는 get_userData 함수는 personID를 입력받고 해당 고객의 닉네임을 반환하는 API를 호출한다. 고객이 로그인할 때 그 고객의 닉네임을 불러주기 위해 만들었다. 고객이 회원가입할 땐는 고객이 직접 닉네임을 입력하기 때문에 이 API가 호출되지 않는다.

ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ

§ 주의 사항 §
1. 카메라 화상에서 고객 얼굴을 감지하는 것은 OpenCV를 통해 구현되었는데, OpenCV에서 얼굴이라고 했으나 MS 서버에서 얼굴이 아니라고 하는 경우가 간혹 생기며, 카메라가 구릴 수록 그 빈도가 높아진다.

2. 클라이언트에서는 Detect API가 반환하는 얼굴 정보 중 몇 가지만 골라 dict 타입으로 가공하도록 하였다. (FaceAPI.py 74~80 Line 참고)

3. 현재 고객정보를 서버로 보내는 코드는 client.py 491~493 Line에 작성되어 있으나 정상 작동하지 않는다.
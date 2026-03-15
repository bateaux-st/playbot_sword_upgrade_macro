"""Game command strings and mode constants."""
MODE_TARGET = "1"
MODE_HIDDEN = "2"
MODE_MONEY = "3"
MODE_FUSION = "4"
FUSION_TARGET_LEVEL = 20
CMD_GIFT = "/선물받기"
CMD_PROFILE = "/프로필"
CMD_ENHANCE = "/강화"
CMD_ADVANCED_ENHANCE = "/상급강화"
CMD_CHECK_IN = "/출석체크"
CMD_BATTLE = "/배틀"
CMD_SWAP = "/교체"
CMD_FUSION = "/합성"
CMD_SELL = "/판매"
CMD_RANKING = "/랭킹"
CMD_COLLECTION = "/도감"
CMD_HELP = "/도움말"
GAME_COMMANDS = (
    {
        "key": "gift",
        "usage": CMD_GIFT,
        "description": "플레이봇 초대 이벤트 보상을 수령합니다.",
    },
    {
        "key": "profile",
        "usage": CMD_PROFILE,
        "description": "내 장착 검, 보관 검, 골드, 별의 파편을 확인합니다.",
    },
    {
        "key": "profile_target",
        "usage": f"{CMD_PROFILE} @유저멘션",
        "description": "다른 유저의 프로필을 조회합니다.",
    },
    {
        "key": "enhance",
        "usage": CMD_ENHANCE,
        "description": "현재 장착 검을 일반 강화합니다.",
    },
    {
        "key": "advanced_enhance",
        "usage": CMD_ADVANCED_ENHANCE,
        "description": "별의 파편을 사용해 현재 장착 검을 상급강화합니다.",
    },
    {
        "key": "check_in",
        "usage": CMD_CHECK_IN,
        "description": "출석체크 보상을 수령합니다.",
    },
    {
        "key": "battle",
        "usage": CMD_BATTLE,
        "description": "랜덤 유저와 배틀합니다.",
    },
    {
        "key": "battle_target",
        "usage": f"{CMD_BATTLE} @유저멘션",
        "description": "지정한 유저와 배틀합니다.",
    },
    {
        "key": "swap",
        "usage": CMD_SWAP,
        "description": "장착 검과 보관 검을 교체합니다.",
    },
    {
        "key": "fusion",
        "usage": CMD_FUSION,
        "description": "20강 장착 검과 보관 검을 이용해 합성을 시도합니다.",
    },
    {
        "key": "sell",
        "usage": CMD_SELL,
        "description": "현재 강화된 검을 판매하고 새 검을 받습니다.",
    },
    {
        "key": "ranking",
        "usage": CMD_RANKING,
        "description": "현재 그룹방 멤버의 랭킹을 확인합니다.",
    },
    {
        "key": "collection",
        "usage": CMD_COLLECTION,
        "description": "내 검 컨렉션을 확인합니다.",
    },
    {
        "key": "collection_target",
        "usage": f"{CMD_COLLECTION} @유저멘션",
        "description": "다른 유저의 검 컨렉션을 확인합니다.",
    },
    {
        "key": "help",
        "usage": CMD_HELP,
        "description": "사용 가능한 명령어 목록을 다시 확인합니다.",
    },
)
GAME_COMMAND_MAP = {item["key"]: item for item in GAME_COMMANDS}
TRASH_WEAPON_KEYWORDS = ("낡은 검", "낡은 몽둥이", "낡은 도끼", "낡은 망치")


def get_mode_label(mode: str) -> str:
    return {
        MODE_TARGET: "target",
        MODE_HIDDEN: "hidden",
        MODE_MONEY: "money",
        MODE_FUSION: "fusion",
    }.get(mode, "unknown")

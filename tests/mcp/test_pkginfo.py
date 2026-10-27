from mcp_servers.common.pkginfo import parse_pkginfo

SAMPLE = """
Loading package: DishonoredGame.upk Ver: 801/30 Engine: 9411 Names: 24432 Exports: 30049 Imports: 652 Game: 800033
Class statistics:
   19 AkBank
  318 AkEvent
"""


def test_parse_summary_and_classes():
    parsed = parse_pkginfo(SAMPLE)
    assert parsed["parsed"] is True
    assert parsed["ue_version"] == "801/30"
    assert parsed["exports"] == 30049
    assert parsed["engine"] == 9411
    names = [item["name"] for item in parsed["class_histogram"]]
    assert names[0] == "AkEvent"


def test_parse_failure_is_explicit():
    assert parse_pkginfo("no summary here")["parsed"] is False

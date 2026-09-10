from app.models import BoardSection, ScriptPackage


def test_locked_pause_copy():
    script = ScriptPackage(
        examiner_question="Right then, doctor. Tell me about amiodarone.",
        pause_screen_top="PAUSE THE VIDEO",
        pause_screen_bottom="THINK LIKE THE CANDIDATE",
        memory_line="Amiodarone is the antiarrhythmic that refuses to pick a lane.",
        formal_answer="Amiodarone is predominantly a class III antiarrhythmic.",
        board_sections=[BoardSection(heading="Mechanism", bullets=["Potassium-channel blockade"])],
    )
    assert script.pause_screen_top == "PAUSE THE VIDEO"
    assert script.pause_screen_bottom == "THINK LIKE THE CANDIDATE"

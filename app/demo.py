"""Playable synthetic style demonstration. Never passes through medical QC."""
import argparse
import json
from pathlib import Path
from app.models import ScriptPackage, BoardSection
from app.render import board
from app.video import assemble

def demo_script():
    return ScriptPackage(
        examiner_question='Right then, doctor. Tell me about your approach to a viva.',
        pause_screen_top='PAUSE THE VIDEO', pause_screen_bottom='THINK LIKE THE CANDIDATE',
        memory_line='A confident opening beats a scenic route to the answer.',
        formal_answer='Start by listening to the question and identifying exactly what is being asked. '
            'Give a clear opening statement, then organise the answer into a few short sections. '
            'Use precise language and keep each point connected to the question. '
            'If you are uncertain, acknowledge that rather than inventing detail. '
            'Finish with a concise summary, then leave space for the next question. '
            'This is a presentation demonstration only, with no drug facts or clinical advice.',
        board_sections=[
            BoardSection(heading='Listen first',bullets=['Identify the question.','Take a breath before answering.']),
            BoardSection(heading='Open clearly',bullets=['Lead with a direct statement.','Give the answer a structure.']),
            BoardSection(heading='Build the answer',bullets=['One point at a time.','Keep the language precise.']),
            BoardSection(heading='Stay honest',bullets=['Acknowledge uncertainty.','Do not invent missing details.']),
            BoardSection(heading='Close well',bullets=['Summarise briefly.','Leave room for follow-up.']),
            BoardSection(heading='Style preview',bullets=['Synthetic narration script.','No medical claims.'])])

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',default='outputs/style-demo')
    args=parser.parse_args()
    out=Path(args.out)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Choose a fresh demo directory')
    out.mkdir(parents=True,exist_ok=True)
    script=demo_script()
    board('The viva, drawn clearly.',script,out/'board.png',demo=True)
    seconds=assemble('The viva, drawn clearly.',script,out,demo=True)
    (out/'script.txt').write_text('\n\n'.join([script.examiner_question,script.memory_line,script.formal_answer]),encoding='utf-8')
    (out/'demo.json').write_text(json.dumps({'synthetic':True,'medical_qc':'not applicable','duration_seconds':seconds},indent=2))
    print(f'Synthetic demonstration rendered: {seconds:.2f}s')

if __name__=='__main__':
    main()

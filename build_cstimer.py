import subprocess, sys

# Read Makefile to extract timerSrc files
with open('Makefile') as f:
    lines = f.readlines()

files = []
in_timer_src = False
for line in lines:
    s = line.rstrip('\n').rstrip('\r')
    if s.startswith('timerSrc = '):
        in_timer_src = True
        rest = s.split('timerSrc = $(addprefix $(src)/js/,', 1)[1]
        rest = rest.replace('\\', '').strip()
        if rest:
            # remove trailing ) if present on first line
            if rest.endswith(')'):
                rest = rest[:-1].strip()
                files.append(rest)
                break
            files.append(rest)
        continue
    if in_timer_src:
        file_part = s.replace('\\', '').strip()
        if file_part.endswith(')'):
            file_part = file_part[:-1].strip()
            if file_part:
                files.append(file_part)
            break
        if file_part:
            files.append(file_part)

files = ['src/js/' + f for f in files]
print('Files:', len(files))
for f in files[:5]:
    print(' ', f)
print('...')
print('Last file:', files[-1])

cmd = [
    'java', '-jar', 'lib/compiler.jar',
    '--use_types_for_optimization', '--language_out', 'STABLE', '--charset', 'UTF-8', '--strict_mode_input',
    "--define=DEBUGM=false", "--define=DEBUGWK=false"
] + files + ['--js_output_file', 'dist/js/cstimer.js']
print('CMD length:', len(cmd))
result = subprocess.run(cmd, capture_output=True, text=True)
print('RC:', result.returncode)
print('STDOUT:')
print(result.stdout[:8000])
print('STDERR:')
print(result.stderr[:8000])
with open('build.log','w') as f:
    f.write('RC: ' + str(result.returncode) + '\n')
    f.write('STDOUT:\n')
    f.write(result.stdout)
    f.write('\nSTDERR:\n')
    f.write(result.stderr)

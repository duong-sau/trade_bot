current_step = 0

bar = ['→', '↘', '↓', '↙', '←', '↖', '↑', '↗']

def step():
    global current_step
    current_step += 1
    if current_step >= 8:
        current_step = 0
    print("\033[D" + bar[current_step], end='', flush=True)
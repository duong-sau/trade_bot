current_step = 0

bar = ['→', '↘', '↓', '↙', '←', '↖', '↑', '↗']

def step(message = "Runnig..."):
    global current_step
    current_step += 1
    if current_step >= 8:
        current_step = 0
    print(f"\r\033[K{bar[current_step]}   {message}", end='', flush=True)
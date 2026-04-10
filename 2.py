for i in range(16, 31):
    with open(f'article/{i}.txt', 'w', encoding='utf-8') as f:
        f.write(f'')
        print(f'已写入 article/{i}.txt')
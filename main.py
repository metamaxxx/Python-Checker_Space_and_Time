import aiohttp
import asyncio

async def check_proxy(session, proxy):
    try:
        async with session.get('https://httpbin.org/ip', proxy=f"http://{proxy}", timeout=5) as response:
            return response.status == 200
    except Exception as e:
        print(f"Прокси {proxy} не работает: {e}")
        return False

async def check_wallet(session, wallet, proxy):
    try:
        async with session.get(f'https://gigaclaim.spaceandtime.io/api/eligibility?address={wallet}', proxy=f"http://{proxy}") as response:
            if response.status == 200:
                data = await response.json()
                total_amount = int(data['totalAmount']) / (10 ** 18)  # Преобразуем в токены
                is_eligible = data['isEligible']
                allocation = total_amount if is_eligible else 0
                return (wallet, allocation)
            else:
                print(f"Error fetching data for wallet {wallet}: {response.status}")
                return (wallet, 0)
    except Exception as e:
        print(f"Ошибка при запросе для {wallet}: {e}")
        return (wallet, 0)

async def main(wallet_file, proxy_file=None):
    results = []
    async with aiohttp.ClientSession() as session:
        # Чтение кошельков
        with open(wallet_file, 'r') as file:
            wallets = [line.strip() for line in file.readlines()]

        # Проверка прокси
        valid_proxies = []
        if proxy_file:
            with open(proxy_file, 'r') as file:
                proxies = [line.strip() for line in file.readlines()]

            if len(wallets) != len(proxies):
                print("Количество кошельков и прокси не совпадает. Проверьте файлы.")
                return

            for proxy in proxies:
                print(f"Проверка прокси: {proxy}")
                if await check_proxy(session, proxy):
                    valid_proxies.append(proxy)
                else:
                    print(f"Прокси {proxy} не работает и будет пропущен.")

            if not valid_proxies:
                print("Нет работающих прокси. Завершение работы.")
                return

        # Проверка кошельков
        tasks = []
        for i, wallet in enumerate(wallets):
            if wallet:
                proxy = valid_proxies[i % len(valid_proxies)]  # Используем валидный прокси
                print(f"Используем прокси для {wallet}: {proxy}")
                tasks.append(check_wallet(session, wallet, proxy))

        results = await asyncio.gather(*tasks)

    return results

def print_results(results):
    print(f"{'Wallet Address':<50} {'Allocation (Tokens)':<20}")
    print("=" * 70)
    for wallet, allocation in results:
        print(f"{wallet:<50} {allocation:<20}")

if __name__ == "__main__":
    wallet_file = 'wallets.txt'
    proxy_file = 'proxies.txt'  # Укажите имя файла с прокси
    results = asyncio.run(main(wallet_file, proxy_file))
    if results:
        print_results(results)
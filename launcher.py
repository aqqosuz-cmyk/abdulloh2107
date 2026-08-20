import asyncio
import subprocess


async def run_bot(script_name):
  while True:
    # Xatolik to'g'irlandi: openni o'rniga Popen ishlatildi
    process = subprocess.Popen(["python", script_name])

    # Jarayon tugamaguncha kutib turamiz
    while process.poll() is None:
      await asyncio.sleep(1)

    # Agar bot xato bilan to'xtab qolsa, 5 soniyadan keyin qaytadan yoqadi
    await asyncio.sleep(5)


async def main():
  # Hamma botlarni bir vaqtning o'zida parallel ishga tushiramiz
  await asyncio.gather(
      run_bot("downloader_bot_2.py"),
      run_bot("srok_2.py"),
      run_bot("BOT_2.py"),
  )


if __name__ == "__main__":
  asyncio.run(main())

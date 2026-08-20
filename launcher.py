import asyncio
import subprocess


async def run_bot(script_name):
  while True:
    process = subprocess.openni(["python", script_name])
    process.wait()
    await asyncio.sleep(5)


async def main():
  # Uchalasini bir vaqtning o'zida fonda ishga tushiramiz
  await asyncio.gather(
      run_bot("downloader_bot_2.py"),
      run_bot("srok_2.py"),
      run_bot("BOT_2.py"),
  )


if __name__ == "__main__":
  asyncio.run(main())
import asyncio
import subprocess


async def run_bot(script_name):
  while True:
    process = subprocess.Popen(["python", script_name])
    while process.poll() is None:
      await asyncio.sleep(1)
    await asyncio.sleep(5)


async def main():
  # GitHub'dagi haqiqiy fayl nomlari yozildi
  await asyncio.gather(
      run_bot("downloader_bot.py"), run_bot("srok.py"), run_bot("BOT.py")
  )


if __name__ == "__main__":
  asyncio.run(main())

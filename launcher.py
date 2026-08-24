import asyncio
import subprocess


async def run_bot(script_name):
  while True:
    process = subprocess.Popen(["python", script_name])
    while process.poll() is None:
      await asyncio.sleep(1)
    await asyncio.sleep(5)


async def main():
  # Barcha botlar, shu jumladan resume.py birga ishga tushiriladi
  await asyncio.gather(
      run_bot("downloader_bot.py"),
      run_bot("srok.py"),
      run_bot("BOT.py"),
      run_bot("resume.py"),
  )


if __name__ == "__main__":
  asyncio.run(main())

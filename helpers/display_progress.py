class Progress:
    def __init__(self, user_id, client, message):
        self.user_id = user_id
        self.client = client
        self.message = message

    async def progress_for_pyrogram(self, current, total, msg, start):
        now = time.time()
        diff = now - start

        if round(diff % 10.00) == 0 or current == total:
            percentage = current * 100 / total
            speed = current / diff
            time_to_completion = (total - current) / speed
            progress = "[{0}{1}] \n**Progress**: {2}%".format(
                ''.join(["●" for _ in range(math.floor(percentage / 5))]),
                ''.join(["○" for _ in range(20 - math.floor(percentage / 5))]),
                round(percentage, 2))
            tmp = progress + "\n**Downloaded**: {0} of {1}\n**Speed**: {2}/s\n**ETA**: {3}".format(
                humanbytes(current),
                humanbytes(total),
                humanbytes(speed),
                TimeFormatter(time_to_completion)
            )
            try:
                await self.message.edit(f"{msg}\n\n{tmp}")
            except Exception as e:
                LOGGER.error(e)

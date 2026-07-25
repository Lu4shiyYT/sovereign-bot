import discord
from discord.ext import commands, tasks
from discord import app_commands
from database import async_fetch_all, async_fetch_one, async_execute, async_get_game_date
import time
import random
import datetime
import asyncio
from zoneinfo import ZoneInfo
import json

try:
    from config import CHANNEL_IDS, BATTLE_ROUND_INTERVAL_MINUTES
except ImportError:
    CHANNEL_IDS = {}
    BATTLE_ROUND_INTERVAL_MINUTES = 30

from data.war_params import (ATTACK_TYPES, EQUIPMENT_POWER, WEAPON_POWER,
                             RECON_BASE_CHANCE, RECON_SUCCESS_REVEAL, RECON_FAIL_REVEAL,
                             REPORT_TEMPLATES)

WAR_START_NEWS = [
    "⚔️ Конфликт начался! {attacker} под руководством {attacker_ruler} объявил войну {defender}!",
    "💥 Внимание! {attacker} и {defender} вступают в войну. {attacker_ruler} заявил о начале боевых действий.",
    "🚀 Военная тревога! {attacker} атакует {defender}. {attacker_ruler} отдал приказ о наступлении.",
    "🌍 Мир раскололся: {attacker} объявил войну {defender}. Правитель {attacker_ruler} выступил с обращением.",
    "🔥 Пламя войны: {attacker} начинает вторжение в {defender}. {attacker_ruler} взял на себя ответственность."
]
WAR_PEACE_NEWS = [
    "🕊️ Мир восстановлен! {country1} и {country2} заключили мирный договор.",
    "✅ Война окончена: {country1} и {country2} пришли к соглашению о прекращении огня.",
    "🤝 Дипломатия победила: {country1} и {country2} подписали мир.",
    "📜 Исторический мир: {country1} и {country2} завершили военный конфликт.",
    "🔚 Конец войны: {country1} и {country2} объявили о перемирии."
]

class War(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_moves_task = None
        print("War cog initialized", flush=True)

    async def cog_load(self):
        print("War cog loaded, starting loops", flush=True)
        if not self.battle_loop.is_running():
            self.battle_loop.start()
        self.bot_moves_task = self.bot.loop.create_task(self._bot_move_scheduler())

    # ---------- Боевой цикл ----------
    @tasks.loop(minutes=BATTLE_ROUND_INTERVAL_MINUTES)
    async def battle_loop(self):
        await self._process_round()

    async def _process_round(self):
        """Обрабатывает все накопленные ходы и вычисляет потери."""
        active_wars = await async_fetch_all("SELECT id, attacker_id, defender_id FROM wars WHERE status='active'")
        for war in active_wars:
            attacker = await async_fetch_one("SELECT * FROM countries WHERE id=?", (war['attacker_id'],))
            defender = await async_fetch_one("SELECT * FROM countries WHERE id=?", (war['defender_id'],))
            if not attacker or not defender:
                continue

            moscow_tz = ZoneInfo("Europe/Moscow")
            now = datetime.datetime.now(moscow_tz)
            if now.minute < 30:
                interval_start = now.replace(minute=0, second=0, microsecond=0)
            else:
                interval_start = now.replace(minute=30, second=0, microsecond=0)
            interval_end = interval_start + datetime.timedelta(minutes=30)

            attacker_moves = await async_fetch_all(
                "SELECT * FROM war_moves WHERE war_id=? AND country_id=? AND created_at >= ? AND created_at < ?",
                (war['id'], attacker['id'], interval_start.timestamp(), interval_end.timestamp())
            )
            defender_moves = await async_fetch_all(
                "SELECT * FROM war_moves WHERE war_id=? AND country_id=? AND created_at >= ? AND created_at < ?",
                (war['id'], defender['id'], interval_start.timestamp(), interval_end.timestamp())
            )

            atk_action = attacker_moves[-1] if attacker_moves else None
            def_action = defender_moves[-1] if defender_moves else None

            # Тактика атакующего
            atk_tactic = "frontal"
            if atk_action and atk_action['move_type'] == 'attack':
                try:
                    details = json.loads(atk_action['details'])
                    atk_tactic = details.get("attack_type", "frontal")
                except:
                    pass
            tactic_data = ATTACK_TYPES.get(atk_tactic, ATTACK_TYPES["frontal"])

            def calc_power(country):
                base = country['army_count'] * (country['combat_capability'] / 100)
                if country['owner_id'] is None:
                    base *= (country.get('bot_strength', 5) / 10)
                return base

            atk_power = calc_power(attacker) * tactic_data["attack_bonus"]
            def_power = calc_power(defender) * tactic_data["defense_penalty"]

            def_loss = min(defender['army_count'], int(atk_power * 0.15))
            atk_loss = min(attacker['army_count'], int(def_power * 0.10))

            await async_execute("UPDATE countries SET army_count = army_count - ? WHERE id=?", (atk_loss, attacker['id']))
            await async_execute("UPDATE countries SET army_count = army_count - ? WHERE id=?", (def_loss, defender['id']))

            # Отправка сводки в новостной канал
            hashtag = f"#{attacker['name'].upper().replace(' ', '')}-{defender['name'].upper().replace(' ', '')}"
            template = random.choice(REPORT_TEMPLATES["round_result"])
            report_text = template.format(
                attacker=attacker['display_name'] or attacker['name'],
                defender=defender['display_name'] or defender['name'],
                atk_loss=atk_loss,
                def_loss=def_loss,
                frontline_status="стабильна",
                hashtag=hashtag
            )
            news_channel_id = CHANNEL_IDS.get("news")
            if news_channel_id:
                channel = self.bot.get_channel(news_channel_id)
                if channel:
                    await channel.send(report_text)

            # Сохраняем отчёт в БД
            await async_execute("INSERT INTO war_reports (war_id, report_text, created_at) VALUES (?, ?, ?)",
                                (war['id'], report_text, time.time()))

            # Завершение войны при нулевой армии
            if attacker['army_count'] <= 0 or defender['army_count'] <= 0:
                winner = attacker if attacker['army_count'] > 0 else defender
                loser = defender if winner == attacker else attacker
                await async_execute("UPDATE wars SET status='ended' WHERE id=?", (war['id'],))
                await self._offer_post_war_terms(war, winner, loser)

    # ---------- Планировщик ходов ботов ----------
    async def _bot_move_scheduler(self):
        """Каждые 5 минут проверяет, есть ли активные войны с ботами, и заставляет бота ходить, если ещё не ходил."""
        while True:
            await asyncio.sleep(300)
            try:
                active_wars = await async_fetch_all("SELECT id, attacker_id, defender_id FROM wars WHERE status='active'")
                moscow_tz = ZoneInfo("Europe/Moscow")
                now = datetime.datetime.now(moscow_tz)
                if now.minute < 30:
                    interval_start = now.replace(minute=0, second=0, microsecond=0)
                else:
                    interval_start = now.replace(minute=30, second=0, microsecond=0)
                interval_end = interval_start + datetime.timedelta(minutes=30)

                for war in active_wars:
                    for side_id in (war['attacker_id'], war['defender_id']):
                        country = await async_fetch_one("SELECT * FROM countries WHERE id=?", (side_id,))
                        if country and country['owner_id'] is None:
                            # Бот
                            existing = await async_fetch_one(
                                "SELECT id FROM war_moves WHERE war_id=? AND country_id=? AND created_at >= ? AND created_at < ?",
                                (war['id'], side_id, interval_start.timestamp(), interval_end.timestamp())
                            )
                            if not existing:
                                action = random.choice(["attack", "defend", "scout", "tactics"])
                                details = json.dumps({"attack_type": random.choice(list(ATTACK_TYPES.keys())), "army_percent": 100})
                                await async_execute(
                                    "INSERT INTO war_moves (war_id, country_id, move_type, details, created_at) VALUES (?, ?, ?, ?, ?)",
                                    (war['id'], side_id, action, details, now.timestamp())
                                )
            except Exception as e:
                print(f"Bot scheduler error: {e}", flush=True)

    # ---------- Команда хода для игрока ----------
    @app_commands.command(name="war_action", description="Совершить ход в войне (доступен раз в 30 мин)")
    @app_commands.describe(
        action="Тип операции",
        attack_type="Вид атаки (если атака)",
        target_army_percent="Процент армии (1-100)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Атака", value="attack"),
        app_commands.Choice(name="Оборона", value="defend"),
        app_commands.Choice(name="Разведка", value="scout"),
        app_commands.Choice(name="Смена тактики", value="tactics")
    ])
    @app_commands.choices(attack_type=[
        app_commands.Choice(name="Лобовая", value="frontal"),
        app_commands.Choice(name="Фланговый удар", value="flank"),
        app_commands.Choice(name="Окружение", value="encircle")
    ])
    async def war_action(self, interaction: discord.Interaction, action: str, attack_type: str = "frontal", target_army_percent: int = 100):
        await interaction.response.defer(ephemeral=True)
        try:
            my_country = await async_fetch_one("SELECT * FROM countries WHERE owner_id=?", (interaction.user.id,))
            if not my_country:
                await interaction.followup.send("Вы не управляете страной.", ephemeral=True)
                return

            war = await async_fetch_one(
                "SELECT id, attacker_id, defender_id FROM wars WHERE (attacker_id=? OR defender_id=?) AND status='active'",
                (my_country['id'], my_country['id'])
            )
            if not war:
                await interaction.followup.send("Вы не находитесь в состоянии войны.", ephemeral=True)
                return

            moscow_tz = ZoneInfo("Europe/Moscow")
            now = datetime.datetime.now(moscow_tz)
            if now.minute < 30:
                interval_start = now.replace(minute=0, second=0, microsecond=0)
            else:
                interval_start = now.replace(minute=30, second=0, microsecond=0)
            interval_end = interval_start + datetime.timedelta(minutes=30)

            existing = await async_fetch_one(
                "SELECT id FROM war_moves WHERE war_id=? AND country_id=? AND created_at >= ? AND created_at < ?",
                (war['id'], my_country['id'], interval_start.timestamp(), interval_end.timestamp())
            )
            if existing:
                await interaction.followup.send("Вы уже отдали приказ в этой половине часа.", ephemeral=True)
                return

            details = json.dumps({"attack_type": attack_type, "army_percent": target_army_percent})
            await async_execute(
                "INSERT INTO war_moves (war_id, country_id, move_type, details, created_at) VALUES (?, ?, ?, ?, ?)",
                (war['id'], my_country['id'], action, details, now.timestamp())
            )

            # Номер хода
            move_num = await async_fetch_one("SELECT COUNT(*) as cnt FROM war_moves WHERE war_id=?", (war['id'],))
            # Противник
            enemy_id = war['attacker_id'] if war['defender_id'] == my_country['id'] else war['defender_id']
            enemy = await async_fetch_one("SELECT name, owner_id FROM countries WHERE id=?", (enemy_id,))

            await interaction.followup.send(
                f"✅ Вы сделали ход №{move_num['cnt']} в войне против **{enemy['name']}**.",
                ephemeral=True
            )

            if enemy and enemy['owner_id']:
                enemy_user = self.bot.get_user(enemy['owner_id'])
                if enemy_user:
                    try:
                        await enemy_user.send(
                            f"⚠️ **{my_country['display_name'] or my_country['name']}** совершил ход в войне против вас."
                        )
                    except discord.Forbidden:
                        pass

            # Разведка / смена тактики
            if action == "scout":
                await self._handle_scout(my_country, enemy, war, interaction)
            elif action == "tactics":
                hashtag = f"#{my_country['name'].upper().replace(' ', '')}-{enemy['name'].upper().replace(' ', '')}"
                tactic_name = ATTACK_TYPES[attack_type]["name"] if attack_type in ATTACK_TYPES else "неизвестная"
                news_channel = self.bot.get_channel(CHANNEL_IDS.get("news", 0))
                if news_channel:
                    await news_channel.send(
                        REPORT_TEMPLATES["tactics_change"].format(
                            country=my_country['display_name'] or my_country['name'],
                            tactic=tactic_name,
                            hashtag=hashtag
                        )
                    )

        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    async def _handle_scout(self, my_country, enemy, war, interaction):
        """Обрабатывает разведку."""
        recon_power = my_country['info_security']
        counter_power = enemy['counter_intelligence'] if enemy['counter_intelligence'] > 0 else 1
        success_chance = RECON_BASE_CHANCE * (recon_power / counter_power)
        success = random.random() < success_chance

        hashtag = f"#{my_country['name'].upper().replace(' ', '')}-{enemy['name'].upper().replace(' ', '')}"
        news_channel = self.bot.get_channel(CHANNEL_IDS.get("news", 0))

        if success:
            equip_summary = await self._get_equipment_summary(enemy['id'])
            report = (
                f"🔍 Разведка {my_country['display_name'] or my_country['name']} обнаружила:\n"
                f"• Армия: {self.format_number(enemy['army_count'])} чел.\n"
                f"• Техника: {equip_summary if equip_summary else 'нет данных'}\n"
                f"#{hashtag}"
            )
            await interaction.followup.send(report, ephemeral=True)
            if news_channel:
                await news_channel.send(REPORT_TEMPLATES["scout_success"].format(
                    country=my_country['display_name'] or my_country['name'],
                    hashtag=hashtag
                ))
        else:
            await interaction.followup.send("❌ Разведка провалилась – группа перехвачена.", ephemeral=True)
            if news_channel:
                await news_channel.send(REPORT_TEMPLATES["scout_fail"].format(
                    country=my_country['display_name'] or my_country['name'],
                    hashtag=hashtag
                ))

    async def _get_equipment_summary(self, country_id):
        assets = await async_fetch_all("SELECT asset_name, quantity FROM military_assets WHERE country_id=? AND asset_type='equipment'", (country_id,))
        if not assets:
            return "отсутствует"
        return ", ".join(f"{a['asset_name']} x{a['quantity']}" for a in assets)

    # ---------- Объявление войны (игрок) ----------
    @app_commands.command(name="declare_war", description="Объявить войну стране, управляемой игроком")
    @app_commands.describe(target="Игрок, управляющий страной")
    async def declare_war_player(self, interaction: discord.Interaction, target: discord.Member):
        await interaction.response.defer(ephemeral=True)
        try:
            if target.id == interaction.user.id:
                await interaction.followup.send("Нельзя объявить войну самому себе!", ephemeral=True)
                return
            my_country = await self._get_country(interaction.user.id)
            if not my_country:
                await interaction.followup.send("Вы не управляете страной.", ephemeral=True)
                return
            target_country = await self._get_country(target.id)
            if not target_country:
                await interaction.followup.send("Этот игрок не управляет страной.", ephemeral=True)
                return
            await self._execute_war_declaration(interaction, my_country, target_country, is_bot=False, target_user=target)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    @app_commands.command(name="declare_war_bot", description="Объявить войну свободной стране (бот)")
    @app_commands.describe(country="Название свободной страны")
    async def declare_war_bot(self, interaction: discord.Interaction, country: str):
        await interaction.response.defer(ephemeral=True)
        try:
            my_country = await self._get_country(interaction.user.id)
            if not my_country:
                await interaction.followup.send("Вы не управляете страной.", ephemeral=True)
                return
            target_country = await async_fetch_one("SELECT * FROM countries WHERE name=? AND owner_id IS NULL", (country,))
            if not target_country:
                await interaction.followup.send("Страна не найдена или уже занята.", ephemeral=True)
                return
            await self._execute_war_declaration(interaction, my_country, target_country, is_bot=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    async def _execute_war_declaration(self, interaction, attacker, defender, is_bot=False, target_user=None):
        existing = await async_fetch_one(
            "SELECT id FROM wars WHERE ((attacker_id=? AND defender_id=?) OR (attacker_id=? AND defender_id=?)) AND status='active'",
            (attacker['id'], defender['id'], defender['id'], attacker['id'])
        )
        if existing:
            await interaction.followup.send("Вы уже воюете с этой страной.", ephemeral=True)
            return

        now = time.time()
        await async_execute(
            "INSERT INTO wars (attacker_id, defender_id, status, start_time) VALUES (?, ?, 'active', ?)",
            (attacker['id'], defender['id'], now)
        )

        attacker_name = attacker['display_name'] or attacker['name']
        defender_name = defender['display_name'] or defender['name']
        attacker_ruler = attacker['ruler_name'] or "Неизвестный правитель"
        defender_ruler = defender['ruler_name'] or "Неизвестный правитель"

        game_date = await async_get_game_date()
        date_str = game_date.strftime("%d.%m.%Y")
        news_template = random.choice(WAR_START_NEWS)
        news_msg = news_template.format(
            attacker=attacker_name, attacker_ruler=attacker_ruler,
            defender=defender_name, defender_ruler=defender_ruler
        )

        war_channel_id = CHANNEL_IDS.get("war_reports")
        channel = None
        if war_channel_id:
            channel = self.bot.get_channel(war_channel_id)
        else:
            channel = await self._get_channel_or_create(interaction.guild, "военные-сводки")
        if channel:
            full_msg = (
                f"# ⚔️ Объявление войны\n\n"
                f"{news_msg}\n\n"
                f"**Дата:** {date_str}\n"
                f"**Силы сторон:** {attacker_name} ({attacker['combat_capability']}) vs {defender_name} ({defender['combat_capability']})\n"
                f"**Численность:** {attacker_name} ({self.format_number(attacker['army_count'])}) vs {defender_name} ({self.format_number(defender['army_count'])})"
            )
            await channel.send(full_msg)

        if not is_bot and defender['owner_id']:
            user = self.bot.get_user(defender['owner_id'])
            if user:
                try:
                    await user.send(f"{interaction.user.mention} объявил вам войну от страны **{attacker_name}**!")
                except discord.Forbidden:
                    pass

        await interaction.followup.send(f"Война объявлена стране {defender_name}.", ephemeral=True)

    @app_commands.command(name="peace_treaty", description="Предложить мир противнику")
    async def peace_treaty(self, interaction: discord.Interaction, target: discord.Member):
        await interaction.response.defer(ephemeral=True)
        if target.id == interaction.user.id:
            await interaction.followup.send("Нельзя заключить мир с самим собой.", ephemeral=True)
            return
        my_country = await self._get_country(interaction.user.id)
        if not my_country:
            await interaction.followup.send("Вы не управляете страной.", ephemeral=True)
            return
        target_country = await self._get_country(target.id)
        if not target_country:
            await interaction.followup.send("Этот игрок не управляет страной.", ephemeral=True)
            return
        war = await async_fetch_one(
            "SELECT id FROM wars WHERE ((attacker_id=? AND defender_id=?) OR (attacker_id=? AND defender_id=?)) AND status='active'",
            (my_country['id'], target_country['id'], target_country['id'], my_country['id'])
        )
        if not war:
            await interaction.followup.send("Вы не находитесь в состоянии войны с этой страной.", ephemeral=True)
            return
        await async_execute("UPDATE wars SET status='ended' WHERE id=?", (war['id'],))

        game_date = await async_get_game_date()
        date_str = game_date.strftime("%d.%m.%Y")
        peace_template = random.choice(WAR_PEACE_NEWS)
        peace_msg = peace_template.format(country1=my_country['name'], country2=target_country['name'])

        war_channel_id = CHANNEL_IDS.get("war_reports")
        if war_channel_id:
            channel = self.bot.get_channel(war_channel_id)
        else:
            channel = await self._get_channel_or_create(interaction.guild, "военные-сводки")
        if channel:
            full_msg = f"# 🕊️ Мирный договор\n\n{peace_msg}\n\n**Дата:** {date_str}"
            await channel.send(full_msg)

        try:
            await target.send(f"{interaction.user.mention} предложил мир от страны **{my_country['name']}**. Война окончена.")
        except discord.Forbidden:
            pass
        await interaction.followup.send(f"Мир заключён с {target_country['name']}.", ephemeral=True)

    # ---------- Методы для game.py ----------
    async def _declare_war(self, interaction: discord.Interaction, attacker_id: int, defender_id: int, is_bot: bool = False):
        await interaction.response.defer(ephemeral=True)
        try:
            attacker = await async_fetch_one("SELECT * FROM countries WHERE id=?", (attacker_id,))
            defender = await async_fetch_one("SELECT * FROM countries WHERE id=?", (defender_id,))
            if not attacker or not defender:
                await interaction.followup.send("Страна не найдена.", ephemeral=True)
                return
            existing = await async_fetch_one(
                "SELECT id FROM wars WHERE ((attacker_id=? AND defender_id=?) OR (attacker_id=? AND defender_id=?)) AND status='active'",
                (attacker_id, defender_id, defender_id, attacker_id)
            )
            if existing:
                await interaction.followup.send("Вы уже воюете с этой страной.", ephemeral=True)
                return
            await self._execute_war_declaration(interaction, attacker, defender, is_bot=is_bot,
                                                target_user=None if is_bot else (await self.bot.fetch_user(defender['owner_id']) if defender['owner_id'] else None))
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    async def _make_peace(self, interaction: discord.Interaction, war_id: int):
        await interaction.response.defer(ephemeral=True)
        try:
            war = await async_fetch_one("SELECT * FROM wars WHERE id=? AND status='active'", (war_id,))
            if not war:
                await interaction.followup.send("Война не найдена или уже завершена.", ephemeral=True)
                return
            my_country = await async_fetch_one("SELECT id, name FROM countries WHERE owner_id=?", (interaction.user.id,))
            if not my_country or (war['attacker_id'] != my_country['id'] and war['defender_id'] != my_country['id']):
                await interaction.followup.send("Вы не участвуете в этой войне.", ephemeral=True)
                return

            await async_execute("UPDATE wars SET status='ended' WHERE id=?", (war_id,))
            attacker = await async_fetch_one("SELECT name FROM countries WHERE id=?", (war['attacker_id'],))
            defender = await async_fetch_one("SELECT name FROM countries WHERE id=?", (war['defender_id'],))
            game_date = await async_get_game_date()
            date_str = game_date.strftime("%d.%m.%Y")
            peace_template = random.choice(WAR_PEACE_NEWS)
            peace_msg = peace_template.format(country1=attacker['name'], country2=defender['name'])

            war_channel_id = CHANNEL_IDS.get("war_reports")
            if war_channel_id:
                channel = self.bot.get_channel(war_channel_id)
            else:
                channel = await self._get_channel_or_create(interaction.guild, "военные-сводки")
            if channel:
                full_msg = f"# 🕊️ Мирный договор\n\n{peace_msg}\n\n**Дата:** {date_str}"
                await channel.send(full_msg)

            enemy_id = war['attacker_id'] if war['defender_id'] == my_country['id'] else war['defender_id']
            enemy = await async_fetch_one("SELECT owner_id, name FROM countries WHERE id=?", (enemy_id,))
            if enemy and enemy['owner_id']:
                target_user = self.bot.get_user(enemy['owner_id'])
                if target_user:
                    try:
                        await target_user.send(f"{interaction.user.mention} предложил мир от страны **{my_country['name']}**. Война окончена.")
                    except discord.Forbidden:
                        pass
            await interaction.followup.send("Мир заключён.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    async def _offer_post_war_terms(self, war, winner, loser):
        if winner['owner_id'] is None:
            return
        user = self.bot.get_user(winner['owner_id'])
        if not user:
            return
        view = PostWarView(war['id'], winner['id'], loser['id'])
        try:
            await user.send(
                f"🎉 Война против **{loser['name']}** окончена вашей победой! Выберите условия:",
                view=view
            )
        except discord.Forbidden:
            pass

    # ---------- Вспомогательные методы ----------
    async def _get_country(self, user_id):
        return await async_fetch_one("SELECT * FROM countries WHERE owner_id=?", (user_id,))

    async def _notify_user(self, user_id, message):
        user = self.bot.get_user(user_id)
        if user:
            try:
                await user.send(message)
            except discord.Forbidden:
                pass

    async def _get_channel_or_create(self, guild, name):
        channel = discord.utils.get(guild.text_channels, name=name)
        if not channel:
            channel = await guild.create_text_channel(name)
        return channel

    def format_number(self, n, decimals=0):
        if n is None:
            return "0"
        if decimals == 0:
            return f"{int(n):,}".replace(",", ".")
        else:
            return f"{n:,.{decimals}f}".replace(",", ".").replace(".", ",", 1)

    async def country_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            rows = await async_fetch_all(
                "SELECT name FROM countries WHERE owner_id IS NULL AND name LIKE ?",
                (f"{current}%",)
            )
            return [app_commands.Choice(name=row['name'], value=row['name']) for row in rows]
        except Exception as e:
            print(f"Ошибка автодополнения стран: {e}", flush=True)
            return []


# ---------- Послевоенное меню ----------
class PostWarView(discord.ui.View):
    def __init__(self, war_id, winner_id, loser_id):
        super().__init__(timeout=86400)
        self.war_id = war_id
        self.winner_id = winner_id
        self.loser_id = loser_id

    @discord.ui.button(label="Аннексировать полностью", style=discord.ButtonStyle.danger)
    async def annex_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await async_execute("UPDATE provinces SET country_id = ? WHERE country_id = ?", (self.winner_id, self.loser_id))
        await async_execute("DELETE FROM countries WHERE id = ?", (self.loser_id,))
        await async_execute("DELETE FROM wars WHERE id = ?", (self.war_id,))
        await interaction.response.edit_message(content="✅ Страна полностью аннексирована. Территория перешла к вам.", view=None)

    @discord.ui.button(label="Забрать определённые регионы", style=discord.ButtonStyle.primary)
    async def take_regions_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⚠️ Выбор регионов появится позже.", ephemeral=True)

    @discord.ui.button(label="Сделать марионеткой", style=discord.ButtonStyle.success)
    async def puppet_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await async_execute("INSERT OR IGNORE INTO puppets (master_id, puppet_id) VALUES (?, ?)", (self.winner_id, self.loser_id))
        await async_execute("DELETE FROM wars WHERE id = ?", (self.war_id,))
        await interaction.response.edit_message(content="✅ Страна стала вашим марионеточным государством.", view=None)

    @discord.ui.button(label="Дополнительные условия", style=discord.ButtonStyle.primary)
    async def extra_terms_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⚠️ Меню дополнительных условий в разработке.", ephemeral=True)

    @discord.ui.button(label="Ничего не делать", style=discord.ButtonStyle.secondary)
    async def nothing_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await async_execute("DELETE FROM wars WHERE id = ?", (self.war_id,))
        await interaction.response.edit_message(content="Вы отказались от требований. Война завершена.", view=None)


async def setup(bot):
    print("Adding War cog...", flush=True)
    await bot.add_cog(War(bot))
    print("War cog added successfully.", flush=True)

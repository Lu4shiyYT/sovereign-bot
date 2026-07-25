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

# ================= КОНСТАНТЫ И ПАРАМЕТРЫ =================
# Тактики атаки
TACTICS = {
    "frontal_assault": {
        "name": "Лобовая атака",
        "attack_mod": 1.0,
        "defense_mod": 1.0,
        "risk": 0.1,
        "description": "Классическое наступление широким фронтом."
    },
    "flanking_maneuver": {
        "name": "Фланговый манёвр",
        "attack_mod": 1.3,
        "defense_mod": 1.2,
        "risk": 0.2,
        "description": "Удар во фланг, ослабляющий оборону."
    },
    "encirclement": {
        "name": "Окружение (котёл)",
        "attack_mod": 1.6,
        "defense_mod": 1.5,
        "risk": 0.4,
        "description": "Попытка взять врага в кольцо. Высокий риск, высокая награда."
    },
    "breakthrough": {
        "name": "Прорыв",
        "attack_mod": 1.8,
        "defense_mod": 1.7,
        "risk": 0.5,
        "description": "Концентрация сил на узком участке для глубокого прорыва."
    },
    "siege": {
        "name": "Осада",
        "attack_mod": 0.7,
        "defense_mod": 0.6,
        "risk": 0.05,
        "description": "Длительная осада укреплённых позиций."
    }
}

# Шаблоны новостей
REPORT_TEMPLATES = {
    "round_result": [
        "⚡ Сводка с фронта: {attacker} атакует {defender}. {attacker} потерял {atk_loss} чел., {defender} потерял {def_loss} чел. Линия фронта: {frontline_status} #{hashtag}",
        "🔥 Бои продолжаются: {attacker} против {defender}. Потери сторон: {atk_loss} и {def_loss} соответственно. #{hashtag}",
        "📡 Военный корреспондент: активная фаза боя завершилась. {attacker} потерял {atk_loss} военнослужащих, {defender} — {def_loss}. #{hashtag}"
    ],
    "scout_success": "🔍 Разведка {country} успешно вскрыла позиции противника! #{hashtag}",
    "scout_fail": "🔇 Попытка разведки {country} провалилась – враг перехватил группу. #{hashtag}",
    "tactics_change": "📋 {country} изменил тактику на {tactic}. #{hashtag}",
    "war_start": [
        "⚔️ Конфликт начался! {attacker} под руководством {attacker_ruler} объявил войну {defender}! #{hashtag}",
        "💥 Внимание! {attacker} и {defender} вступают в войну. {attacker_ruler} заявил о начале боевых действий. #{hashtag}",
        "🚀 Военная тревога! {attacker} атакует {defender}. {attacker_ruler} отдал приказ о наступлении. #{hashtag}",
        "🌍 Мир раскололся: {attacker} объявил войну {defender}. Правитель {attacker_ruler} выступил с обращением. #{hashtag}",
        "🔥 Пламя войны: {attacker} начинает вторжение в {defender}. {attacker_ruler} взял на себя ответственность. #{hashtag}"
    ],
    "peace_offer": "🕊️ {country} предлагает мир {enemy}. Ожидается ответ. #{hashtag}",
    "peace_accepted": "🕊️ Мир восстановлен! {country1} и {country2} заключили мирный договор. #{hashtag}",
    "peace_rejected": "🚫 {country} отклонил предложение мира от {enemy}. Война продолжается. #{hashtag}"
}

class War(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_moves_task = None
        self.pending_peace_offers = {}  # war_id -> {from_country, to_country, timeout}
        print("War cog initialized", flush=True)

    async def cog_load(self):
        print("War cog loaded, starting loops", flush=True)
        if not self.battle_loop.is_running():
            self.battle_loop.start()
        self.bot_moves_task = self.bot.loop.create_task(self._bot_move_scheduler())

    # ================= БОЕВОЙ ЦИКЛ =================
    @tasks.loop(minutes=BATTLE_ROUND_INTERVAL_MINUTES)
    async def battle_loop(self):
        await self._process_round()

    async def _process_round(self):
        """Обрабатывает все накопленные ходы и вычисляет потери."""
        active_wars = await async_fetch_all("SELECT id, attacker_id, defender_id FROM wars WHERE status='active'")
        moscow_tz = ZoneInfo("Europe/Moscow")
        now = datetime.datetime.now(moscow_tz)
        if now.minute < 30:
            interval_start = now.replace(minute=0, second=0, microsecond=0)
        else:
            interval_start = now.replace(minute=30, second=0, microsecond=0)
        interval_end = interval_start + datetime.timedelta(minutes=30)

        for war in active_wars:
            attacker = await async_fetch_one("SELECT * FROM countries WHERE id=?", (war['attacker_id'],))
            defender = await async_fetch_one("SELECT * FROM countries WHERE id=?", (war['defender_id'],))
            if not attacker or not defender:
                continue

            # Получаем ходы сторон в этом интервале
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

            # Если оба не сделали ход, бой не происходит
            if not atk_action and not def_action:
                continue

            # Тактика атакующего
            atk_tactic = "frontal_assault"
            if atk_action and atk_action['move_type'] in ('attack', 'defend', 'tactics'):
                try:
                    details = json.loads(atk_action['details'])
                    atk_tactic = details.get("attack_type", "frontal_assault")
                except:
                    pass
            tactic_data = TACTICS.get(atk_tactic, TACTICS["frontal_assault"])

            # Сила сторон с учётом техники
            atk_equip = await self._get_equipment_power(attacker['id'])
            def_equip = await self._get_equipment_power(defender['id'])

            def calc_power(country, equip_bonus):
                base = country['army_count'] * (country['combat_capability'] / 100)
                if country['owner_id'] is None:
                    base *= (country.get('bot_strength', 5) / 10)
                return base * (1 + equip_bonus / 100)

            atk_power = calc_power(attacker, atk_equip) * tactic_data["attack_mod"]
            def_power = calc_power(defender, def_equip) * tactic_data["defense_mod"]

            # Потери армии
            def_loss = min(defender['army_count'], int(atk_power * 0.15))
            atk_loss = min(attacker['army_count'], int(def_power * 0.10))

            await async_execute("UPDATE countries SET army_count = army_count - ? WHERE id=?", (atk_loss, attacker['id']))
            await async_execute("UPDATE countries SET army_count = army_count - ? WHERE id=?", (def_loss, defender['id']))

            # Потери техники
            atk_equip_losses = self._distribute_equipment_losses(attacker['id'], atk_loss, atk_equip)
            def_equip_losses = self._distribute_equipment_losses(defender['id'], def_loss, def_equip)
            await self._apply_equipment_losses(attacker['id'], atk_equip_losses)
            await self._apply_equipment_losses(defender['id'], def_equip_losses)

            # Хештег и новость
            hashtag = f"#{attacker['name'].upper().replace(' ', '')}-{defender['name'].upper().replace(' ', '')}"
            template = random.choice(REPORT_TEMPLATES["round_result"])
            report_text = template.format(
                attacker=attacker['display_name'] or attacker['name'],
                defender=defender['display_name'] or defender['name'],
                atk_loss=atk_loss,
                def_loss=def_loss,
                frontline_status=self._get_frontline_status(war['id']),
                hashtag=hashtag
            )
            news_channel_id = CHANNEL_IDS.get("news")
            if news_channel_id:
                channel = self.bot.get_channel(news_channel_id)
                if channel:
                    await channel.send(report_text)

            # Сохраняем отчёт
            await async_execute("INSERT INTO war_reports (war_id, report_text, created_at) VALUES (?, ?, ?)",
                                (war['id'], report_text, time.time()))

            # Проверка завершения войны
            if attacker['army_count'] <= 0 or defender['army_count'] <= 0:
                winner = attacker if attacker['army_count'] > 0 else defender
                loser = defender if winner == attacker else attacker
                await async_execute("UPDATE wars SET status='ended' WHERE id=?", (war['id'],))
                await self._offer_post_war_terms(war, winner, loser)

    # ================= КАРТА И ФРОНТ =================
    def _get_frontline_status(self, war_id):
        """Возвращает описание линии фронта на основе провинций."""
        # Заглушка: в будущем можно сравнивать контроль над провинциями
        return "стабильна"

    # ================= ТЕХНИКА =================
    async def _get_equipment_power(self, country_id):
        """Суммирует бонус от техники."""
        assets = await async_fetch_all(
            "SELECT asset_name, quantity FROM military_assets WHERE country_id=? AND asset_type='equipment'",
            (country_id,)
        )
        total = 0
        for a in assets:
            name = a['asset_name']
            qty = a['quantity']
            # Простейшие коэффициенты (можно расширить)
            if "танк" in name:
                total += qty * 2.0
            elif "БМП" in name or "БТР" in name:
                total += qty * 1.5
            elif "самоход" in name or "РСЗО" in name:
                total += qty * 2.2
            elif "истребитель" in name:
                total += qty * 3.0
            elif "бомбардировщик" in name:
                total += qty * 4.0
            elif "вертолёт" in name:
                total += qty * 2.5
            elif "корабль" in name or "авианосец" in name:
                total += qty * 5.0
            else:
                total += qty * 0.5
        return total

    def _distribute_equipment_losses(self, country_id, army_loss, equipment_power):
        """Пропорционально распределяет потери техники."""
        # Заглушка: потери техники не реализованы (можно добавить)
        return {}

    async def _apply_equipment_losses(self, country_id, losses):
        for name, loss in losses.items():
            await async_execute(
                "UPDATE military_assets SET quantity = quantity - ? WHERE country_id=? AND asset_name=? AND asset_type='equipment'",
                (loss, country_id, name)
            )

    # ================= РАЗВЕДКА =================
    async def _handle_scout(self, my_country, enemy, war, interaction):
        recon_power = my_country['info_security'] + random.randint(-10, 10)
        counter_power = enemy['counter_intelligence'] + random.randint(-5, 5)
        if counter_power <= 0:
            counter_power = 1
        success_chance = max(0.1, min(0.9, 0.5 * (recon_power / counter_power)))
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
        assets = await async_fetch_all(
            "SELECT asset_name, quantity FROM military_assets WHERE country_id=? AND asset_type='equipment'",
            (country_id,)
        )
        if not assets:
            return "отсутствует"
        return ", ".join(f"{a['asset_name']} x{a['quantity']}" for a in assets)

    # ================= ХОДЫ БОТОВ =================
    async def _bot_move_scheduler(self):
        while True:
            await asyncio.sleep(300)  # каждые 5 минут
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
                            existing = await async_fetch_one(
                                "SELECT id FROM war_moves WHERE war_id=? AND country_id=? AND created_at >= ? AND created_at < ?",
                                (war['id'], side_id, interval_start.timestamp(), interval_end.timestamp())
                            )
                            if not existing:
                                action = random.choice(["attack", "defend", "scout", "tactics"])
                                tactic = random.choice(list(TACTICS.keys()))
                                details = json.dumps({"attack_type": tactic, "army_percent": 100})
                                await async_execute(
                                    "INSERT INTO war_moves (war_id, country_id, move_type, details, created_at) VALUES (?, ?, ?, ?, ?)",
                                    (war['id'], side_id, action, details, now.timestamp())
                                )
            except Exception as e:
                print(f"Bot scheduler error: {e}", flush=True)

    # ================= КОМАНДА ХОДА =================
    @app_commands.command(name="war_action", description="Совершить ход в войне (раз в 30 мин)")
    @app_commands.describe(
        action="Тип операции",
        attack_type="Тактика атаки",
        target_army_percent="Процент армии (1-100)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Атака", value="attack"),
        app_commands.Choice(name="Оборона", value="defend"),
        app_commands.Choice(name="Разведка", value="scout"),
        app_commands.Choice(name="Смена тактики", value="tactics")
    ])
    @app_commands.choices(attack_type=[
        app_commands.Choice(name="Лобовая атака", value="frontal_assault"),
        app_commands.Choice(name="Фланговый манёвр", value="flanking_maneuver"),
        app_commands.Choice(name="Окружение (котёл)", value="encirclement"),
        app_commands.Choice(name="Прорыв", value="breakthrough"),
        app_commands.Choice(name="Осада", value="siege")
    ])
    async def war_action(self, interaction: discord.Interaction, action: str, attack_type: str = "frontal_assault", target_army_percent: int = 100):
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

            # Проверка времени
            moscow_tz = ZoneInfo("Europe/Moscow")
            now = datetime.datetime.now(moscow_tz)
            if now.minute < 30:
                interval_start = now.replace(minute=0, second=0, microsecond=0)
            else:
                interval_start = now.replace(minute=30, second=0, microsecond=0)

            existing = await async_fetch_one(
                "SELECT id FROM war_moves WHERE war_id=? AND country_id=? AND created_at >= ? AND created_at < ?",
                (war['id'], my_country['id'], interval_start.timestamp(), interval_start.timestamp() + 1800)
            )
            if existing:
                await interaction.followup.send("Вы уже отдали приказ в этой половине часа.", ephemeral=True)
                return

            details = json.dumps({"attack_type": attack_type, "army_percent": target_army_percent})
            await async_execute(
                "INSERT INTO war_moves (war_id, country_id, move_type, details, created_at) VALUES (?, ?, ?, ?, ?)",
                (war['id'], my_country['id'], action, details, now.timestamp())
            )

            # Определяем противника
            enemy_id = war['attacker_id'] if war['defender_id'] == my_country['id'] else war['defender_id']
            enemy = await async_fetch_one("SELECT name, owner_id FROM countries WHERE id=?", (enemy_id,))

            # Номер хода
            move_num = await async_fetch_one("SELECT COUNT(*) as cnt FROM war_moves WHERE war_id=?", (war['id'],))
            await interaction.followup.send(
                f"✅ Вы сделали ход №{move_num['cnt']} в войне против **{enemy['name']}**.",
                ephemeral=True
            )

            # Уведомление противнику
            if enemy and enemy['owner_id']:
                enemy_user = self.bot.get_user(enemy['owner_id'])
                if enemy_user:
                    try:
                        await enemy_user.send(
                            f"⚠️ **{my_country['display_name'] or my_country['name']}** совершил ход в войне против вас."
                        )
                    except discord.Forbidden:
                        pass

            # Если оба сделали ход – немедленная симуляция
            enemy_moves = await async_fetch_one(
                "SELECT id FROM war_moves WHERE war_id=? AND country_id=? AND created_at >= ? AND created_at < ?",
                (war['id'], enemy_id, interval_start.timestamp(), interval_start.timestamp() + 1800)
            )
            if enemy_moves:
                # Оба походили – запускаем обработку раунда для этой войны
                await self._process_single_war(war, interval_start.timestamp())

            # Специальные действия
            if action == "scout":
                await self._handle_scout(my_country, enemy, war, interaction)
            elif action == "tactics":
                hashtag = f"#{my_country['name'].upper().replace(' ', '')}-{enemy['name'].upper().replace(' ', '')}"
                tactic_name = TACTICS[attack_type]["name"]
                news_channel = self.bot.get_channel(CHANNEL_IDS.get("news", 0))
                if news_channel:
                    await news_channel.send(REPORT_TEMPLATES["tactics_change"].format(
                        country=my_country['display_name'] or my_country['name'],
                        tactic=tactic_name,
                        hashtag=hashtag
                    ))

        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    async def _process_single_war(self, war, interval_start):
        """Обрабатывает конкретную войну, когда оба игрока сделали ход."""
        # Копия логики из _process_round, но только для одной войны
        # (можно вызвать _process_round с фильтрацией, но для простоты пока так)
        await self._process_round()

    # ================= ОБЪЯВЛЕНИЕ ВОЙНЫ =================
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
        """Общая логика объявления войны."""
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
        hashtag = f"#{attacker['name'].upper().replace(' ', '')}-{defender['name'].upper().replace(' ', '')}"

        news_template = random.choice(REPORT_TEMPLATES["war_start"])
        news_msg = news_template.format(
            attacker=attacker_name, attacker_ruler=attacker['ruler_name'] or "Неизвестный правитель",
            defender=defender_name, defender_ruler=defender['ruler_name'] or "Неизвестный правитель",
            hashtag=hashtag
        )

        # Отправка в военный канал
        war_channel_id = CHANNEL_IDS.get("war_reports")
        if war_channel_id:
            channel = self.bot.get_channel(war_channel_id)
        else:
            channel = await self._get_channel_or_create(interaction.guild, "военные-сводки")
        if channel:
            await channel.send(news_msg)

        # Уведомление игроку-защитнику
        if not is_bot and defender['owner_id']:
            user = self.bot.get_user(defender['owner_id'])
            if user:
                try:
                    await user.send(f"{interaction.user.mention} объявил вам войну от страны **{attacker_name}**!")
                except discord.Forbidden:
                    pass

        await interaction.followup.send(f"✅ Война объявлена стране {defender_name}.", ephemeral=True)

    # ================= МИРНЫЕ ПЕРЕГОВОРЫ =================
    @app_commands.command(name="peace_treaty", description="Предложить мир противнику")
    async def peace_treaty(self, interaction: discord.Interaction, target: discord.Member):
        await interaction.response.defer(ephemeral=True)
        try:
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

            # Проверяем, не предлагал ли уже мир в этом интервале
            if war['id'] in self.pending_peace_offers:
                await interaction.followup.send("Предложение мира уже отправлено, ожидайте ответа.", ephemeral=True)
                return

            hashtag = f"#{my_country['name'].upper().replace(' ', '')}-{target_country['name'].upper().replace(' ', '')}"
            self.pending_peace_offers[war['id']] = {
                "from": my_country['id'],
                "to": target_country['id'],
                "time": time.time()
            }

            # Отправляем запрос противнику
            if target_country['owner_id']:  # игрок
                user = self.bot.get_user(target_country['owner_id'])
                if user:
                    view = PeaceResponseView(war['id'], my_country['id'], target_country['id'], self)
                    try:
                        await user.send(
                            f"🕊️ **{my_country['display_name'] or my_country['name']}** предлагает мир. Принять?",
                            view=view
                        )
                        await interaction.followup.send("Предложение мира отправлено.", ephemeral=True)
                    except discord.Forbidden:
                        await interaction.followup.send("Не удалось отправить предложение (ЛС закрыты).", ephemeral=True)
                else:
                    await interaction.followup.send("Игрок не найден.", ephemeral=True)
            else:  # бот – принимает решение автоматически с шансом
                await self._bot_peace_decision(war['id'], my_country, target_country, interaction)

        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    async def _bot_peace_decision(self, war_id, my_country, target_country, interaction):
        """Бот принимает решение о мире на основе соотношения сил."""
        attacker = await async_fetch_one("SELECT * FROM countries WHERE id=?", (target_country['id'],))
        # Шанс принятия: если бот проигрывает (армия меньше), шанс выше
        my_army = my_country['army_count']
        bot_army = attacker['army_count']
        if bot_army <= 0:
            acceptance_chance = 1.0
        else:
            ratio = my_army / max(bot_army, 1)
            acceptance_chance = min(0.9, max(0.1, 0.5 + (ratio - 1) * 0.2))

        if random.random() < acceptance_chance:
            # Бот согласен
            await async_execute("UPDATE wars SET status='ended' WHERE id=?", (war_id,))
            self.pending_peace_offers.pop(war_id, None)
            hashtag = f"#{my_country['name'].upper().replace(' ', '')}-{target_country['name'].upper().replace(' ', '')}"
            news_msg = REPORT_TEMPLATES["peace_accepted"].format(
                country1=my_country['display_name'] or my_country['name'],
                country2=target_country['display_name'] or target_country['name'],
                hashtag=hashtag
            )
            await self._send_news(news_msg)
            await interaction.followup.send("✅ Бот принял ваше предложение мира.", ephemeral=True)
        else:
            # Бот отказался
            self.pending_peace_offers.pop(war_id, None)
            hashtag = f"#{my_country['name'].upper().replace(' ', '')}-{target_country['name'].upper().replace(' ', '')}"
            news_msg = REPORT_TEMPLATES["peace_rejected"].format(
                country=target_country['display_name'] or target_country['name'],
                enemy=my_country['display_name'] or my_country['name'],
                hashtag=hashtag
            )
            await self._send_news(news_msg)
            await interaction.followup.send("❌ Бот отклонил предложение мира.", ephemeral=True)

    # ================= МЕТОДЫ ДЛЯ VIEW (из game.py) =================
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
        """Принудительное завершение войны (используется редко)."""
        await interaction.response.defer(ephemeral=True)
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
        hashtag = f"#{attacker['name'].upper().replace(' ', '')}-{defender['name'].upper().replace(' ', '')}"
        news_msg = REPORT_TEMPLATES["peace_accepted"].format(
            country1=attacker['name'], country2=defender['name'], hashtag=hashtag
        )
        await self._send_news(news_msg)
        await interaction.followup.send("Мир заключён.", ephemeral=True)

    async def _send_news(self, message):
        """Отправляет сообщение в канал новостей."""
        news_channel_id = CHANNEL_IDS.get("news")
        if news_channel_id:
            channel = self.bot.get_channel(news_channel_id)
            if channel:
                await channel.send(message)

    # ================= УВЕДОМЛЕНИЕ ПРИ РЕГИСТРАЦИИ =================
    async def _notify_country_at_war(self, interaction: discord.Interaction, country_id: int):
        """Проверяет, находится ли страна в войне, и сообщает игроку."""
        wars = await async_fetch_all(
            "SELECT w.id, CASE WHEN w.attacker_id=? THEN w.defender_id ELSE w.attacker_id END AS enemy_id "
            "FROM wars w WHERE (w.attacker_id=? OR w.defender_id=?) AND w.status='active'",
            (country_id, country_id, country_id)
        )
        if not wars:
            return
        enemies = []
        for w in wars:
            enemy = await async_fetch_one("SELECT name FROM countries WHERE id=?", (w['enemy_id'],))
            if enemy:
                enemies.append(enemy['name'])
        if enemies:
            await interaction.followup.send(
                f"⚠️ Ваша страна находится в состоянии войны против: {', '.join(enemies)}.",
                ephemeral=True
            )

    # ================= ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ =================
    async def _get_country(self, user_id):
        return await async_fetch_one("SELECT * FROM countries WHERE owner_id=?", (user_id,))

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


# ================= VIEW ДЛЯ ПОДТВЕРЖДЕНИЯ МИРА =================
class PeaceResponseView(discord.ui.View):
    def __init__(self, war_id, from_country_id, to_country_id, war_cog):
        super().__init__(timeout=86400)
        self.war_id = war_id
        self.from_country_id = from_country_id
        self.to_country_id = to_country_id
        self.war_cog = war_cog

    @discord.ui.button(label="Принять мир", style=discord.ButtonStyle.success)
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Проверяем, что это именно тот игрок, которому предложили
        country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not country or country['id'] != self.to_country_id:
            await interaction.response.send_message("Это предложение не вам.", ephemeral=True)
            return

        await async_execute("UPDATE wars SET status='ended' WHERE id=? AND status='active'", (self.war_id,))
        self.war_cog.pending_peace_offers.pop(self.war_id, None)

        attacker = await async_fetch_one("SELECT name FROM countries WHERE id=?", (self.from_country_id,))
        defender = await async_fetch_one("SELECT name FROM countries WHERE id=?", (self.to_country_id,))
        hashtag = f"#{attacker['name'].upper().replace(' ', '')}-{defender['name'].upper().replace(' ', '')}"
        news_msg = REPORT_TEMPLATES["peace_accepted"].format(
            country1=attacker['name'], country2=defender['name'], hashtag=hashtag
        )
        await self.war_cog._send_news(news_msg)
        await interaction.response.edit_message(content="✅ Вы приняли мир. Война окончена.", view=None)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.danger)
    async def decline_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not country or country['id'] != self.to_country_id:
            await interaction.response.send_message("Это предложение не вам.", ephemeral=True)
            return

        self.war_cog.pending_peace_offers.pop(self.war_id, None)
        attacker = await async_fetch_one("SELECT name FROM countries WHERE id=?", (self.from_country_id,))
        defender = await async_fetch_one("SELECT name FROM countries WHERE id=?", (self.to_country_id,))
        hashtag = f"#{attacker['name'].upper().replace(' ', '')}-{defender['name'].upper().replace(' ', '')}"
        news_msg = REPORT_TEMPLATES["peace_rejected"].format(
            country=defender['name'], enemy=attacker['name'], hashtag=hashtag
        )
        await self.war_cog._send_news(news_msg)
        await interaction.response.edit_message(content="Вы отклонили предложение мира.", view=None)


# ================= ПОСЛЕВОЕННОЕ МЕНЮ =================
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

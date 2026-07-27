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

from data.war_params import TACTICS, WAR_REASONS, WAR_START_NEWS, WAR_PEACE_NEWS, REPORT_TEMPLATES
from data.provinces import PROVINCES_DATA, TERRAIN_MODIFIERS
from data.military import MILITARY_EQUIPMENT, WEAPONS

class War(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_moves_task = None
        self.pending_peace_offers = {}
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
        active_wars = await async_fetch_all("SELECT id, attacker_id, defender_id FROM wars WHERE status='active'")
        moscow_tz = ZoneInfo("Europe/Moscow")
        now = datetime.datetime.now(moscow_tz)
        if now.minute < 30:
            interval_start = now.replace(minute=0, second=0, microsecond=0)
        else:
            interval_start = now.replace(minute=30, second=0, microsecond=0)

        for war in active_wars:
            attacker = await async_fetch_one("SELECT * FROM countries WHERE id=?", (war['attacker_id'],))
            defender = await async_fetch_one("SELECT * FROM countries WHERE id=?", (war['defender_id'],))
            if not attacker or not defender:
                continue

            attacker_moves = await async_fetch_all(
                "SELECT * FROM war_moves WHERE war_id=? AND country_id=? AND created_at >= ? AND created_at < ?",
                (war['id'], attacker['id'], interval_start.timestamp(), interval_start.timestamp() + 1800)
            )
            defender_moves = await async_fetch_all(
                "SELECT * FROM war_moves WHERE war_id=? AND country_id=? AND created_at >= ? AND created_at < ?",
                (war['id'], defender['id'], interval_start.timestamp(), interval_start.timestamp() + 1800)
            )

            atk_action = attacker_moves[-1] if attacker_moves else None
            def_action = defender_moves[-1] if defender_moves else None

            if not atk_action and not def_action:
                continue

            # Определяем провинцию, где идёт бой (пока первая попавшаяся)
            frontline_province = await self._get_frontline_province(war['id'])
            terrain = TERRAIN_MODIFIERS.get(frontline_province['terrain_type'], TERRAIN_MODIFIERS["plain"])

            # Тактика атакующего
            atk_tactic = "frontal_assault"
            if atk_action and atk_action['move_type'] in ('attack', 'defend', 'tactics'):
                try:
                    details = json.loads(atk_action['details'])
                    atk_tactic = details.get("attack_type", "frontal_assault")
                except:
                    pass
            tactic_data = TACTICS.get(atk_tactic, TACTICS["frontal_assault"])

            # Бонус от техники
            atk_equip = await self._get_equipment_power(attacker['id'])
            def_equip = await self._get_equipment_power(defender['id'])

            # Офицеры
            atk_officer = await self._get_officer_bonus(attacker['id'])
            def_officer = await self._get_officer_bonus(defender['id'])

            # Погода в текущей провинции
            weather_mod = await self._get_weather_modifier(frontline_province['id'])

            def calc_power(country, equip_bonus, is_attacker=True):
                base = country['army_count'] * (country['combat_capability'] / 100)
                if country['owner_id'] is None:
                    base *= (country.get('bot_strength', 5) / 10)
                terrain_mult = terrain["attack"] if is_attacker else terrain["defense"]
                return base * (1 + equip_bonus / 100) * terrain_mult * weather_mod * (atk_officer if is_attacker else def_officer)

            atk_power = calc_power(attacker, atk_equip, is_attacker=True) * tactic_data["attack_mod"]
            def_power = calc_power(defender, def_equip, is_attacker=False) * tactic_data["defense_mod"]

            def_loss = min(defender['army_count'], int(atk_power * 0.15))
            atk_loss = min(attacker['army_count'], int(def_power * 0.10))

            await async_execute("UPDATE countries SET army_count = army_count - ? WHERE id=?", (atk_loss, attacker['id']))
            await async_execute("UPDATE countries SET army_count = army_count - ? WHERE id=?", (def_loss, defender['id']))

            # Сдвиг линии фронта
            await self._shift_frontline(war['id'], attacker, defender, atk_power, def_power)

            # Отправка сводки в канал новостей
            template = random.choice(REPORT_TEMPLATES["round_result"])
            report_text = template.format(
                attacker=attacker['display_name'] or attacker['name'],
                defender=defender['display_name'] or defender['name'],
                atk_loss=atk_loss,
                def_loss=def_loss,
                frontline_status="изменилась"
            )
            await self._send_news(report_text)

            # Сохраняем отчёт
            await async_execute("INSERT INTO war_reports (war_id, report_text, created_at) VALUES (?, ?, ?)",
                                (war['id'], report_text, time.time()))

            # Партизанская активность
            await self._check_partisan_activity(war['id'])
            
            if attacker['army_count'] <= 0 or defender['army_count'] <= 0:
                winner = attacker if attacker['army_count'] > 0 else defender
                loser = defender if winner == attacker else attacker
                await async_execute("UPDATE wars SET status='ended' WHERE id=?", (war['id'],))
                await self._offer_post_war_terms(war, winner, loser)

    # ================= КАРТА =================
    async def _get_frontline_province(self, war_id):
        row = await async_fetch_one(
            "SELECT p.* FROM frontlines f JOIN provinces p ON f.province_id = p.id WHERE f.war_id = ? LIMIT 1",
            (war_id,)
        )
        if not row:
            war = await async_fetch_one("SELECT attacker_id, defender_id FROM wars WHERE id=?", (war_id,))
            row = await async_fetch_one(
                "SELECT * FROM provinces WHERE country_id IN (?, ?) LIMIT 1",
                (war['attacker_id'], war['defender_id'])
            )
        return row or {"terrain_type": "plain"}

    async def _shift_frontline(self, war_id, attacker, defender, atk_power, def_power):
        if atk_power > def_power * 1.2:
            provinces = await async_fetch_all("SELECT id FROM provinces WHERE country_id = ?", (defender['id'],))
            if provinces:
                target = random.choice(provinces)
                await async_execute(
                    "INSERT OR REPLACE INTO frontlines (war_id, province_id, controlled_by_id, last_change) VALUES (?, ?, ?, ?)",
                    (war_id, target['id'], attacker['id'], time.time())
                )
                await async_execute("UPDATE provinces SET country_id = ? WHERE id = ?", (attacker['id'], target['id']))
        elif def_power > atk_power * 1.2:
            provinces = await async_fetch_all("SELECT id FROM provinces WHERE country_id = ?", (attacker['id'],))
            if provinces:
                target = random.choice(provinces)
                await async_execute(
                    "INSERT OR REPLACE INTO frontlines (war_id, province_id, controlled_by_id, last_change) VALUES (?, ?, ?, ?)",
                    (war_id, target['id'], defender['id'], time.time())
                )
                await async_execute("UPDATE provinces SET country_id = ? WHERE id = ?", (defender['id'], target['id']))

    # ================= ТЕХНИКА =================
    async def _get_equipment_power(self, country_id):
        assets = await async_fetch_all(
            "SELECT asset_name, quantity FROM military_assets WHERE country_id=? AND asset_type='equipment'",
            (country_id,)
        )
        total = 0
        for a in assets:
            # ищем в MILITARY_EQUIPMENT
            for cat, items in MILITARY_EQUIPMENT.items():
                for item in items:
                    if item['name'] == a['asset_name']:
                        total += item['power'] * a['quantity']
                        break
        return total

        # ================= ПРОИЗВОДСТВО И СНАБЖЕНИЕ =================
    async def _produce_equipment(self, country_id, equipment_name, quantity):
        """Производит технику/оружие на заводах, тратя ресурсы."""
        # Ищем предмет в справочнике
        item_data = None
        for cat, items in {**MILITARY_EQUIPMENT, **WEAPONS}.items():
            for item in items:
                if item['name'] == equipment_name:
                    item_data = item
                    break
            if item_data: break
        if not item_data:
            return False, "Предмет не найден."

        # Проверка ресурсов (заглушка — нужны деньги и металл)
        money = await async_fetch_one("SELECT amount FROM resources WHERE country_id=? AND resource_name='Доллары'", (country_id,))
        if not money or money['amount'] < item_data['cost'] * quantity:
            return False, "Недостаточно долларов."

        # Тратим деньги
        await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name='Доллары'",
                            (item_data['cost'] * quantity, country_id))

        # Добавляем технику/оружие
        existing = await async_fetch_one(
            "SELECT id, quantity FROM military_assets WHERE country_id=? AND asset_name=? AND asset_type='equipment'",
            (country_id, equipment_name))
        if existing:
            await async_execute("UPDATE military_assets SET quantity = quantity + ? WHERE id=?",
                                (quantity, existing['id']))
        else:
            await async_execute(
                "INSERT INTO military_assets (country_id, asset_type, asset_name, quantity) VALUES (?, 'equipment', ?, ?)",
                (country_id, equipment_name, quantity))
        return True, f"Произведено {quantity} ед. {equipment_name}."

    async def _consume_supplies(self, country_id, army_percent, action_type):
        """Расходует топливо и боеприпасы пропорционально армии."""
        country = await async_fetch_one("SELECT * FROM countries WHERE id=?", (country_id,))
        army_count = country['army_count']
        used_army = int(army_count * army_percent / 100)
        # Пока просто заглушка: тратим условные единицы "Припасы"
        await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name='Продовольствие'",
                            (int(used_army * 0.01), country_id))

    # ================= ОФИЦЕРСКИЙ КОРПУС =================
    async def _get_officer_bonus(self, country_id):
        officers = await async_fetch_all("SELECT * FROM officers WHERE country_id=?", (country_id,))
        if not officers:
            return 1.0  # без бонуса
        # Средний навык атаки
        avg_attack = sum(o['attack_skill'] for o in officers) / len(officers)
        return 1.0 + (avg_attack * 0.1)  # до +10%

    # ================= ПОГОДА =================
    async def _get_weather_modifier(self, province_id):
        """Возвращает множитель погоды (0.8 - 1.2) для данного региона."""
        row = await async_fetch_one("SELECT * FROM weather_log WHERE province_id=? ORDER BY id DESC LIMIT 1",
                                    (province_id,))
        if not row:
            return 1.0
        # Упрощённо: температура и осадки влияют на атаку
        temp_mod = 1.0 + (row['temperature'] - 20) * 0.005
        precip_mod = 1.0 - row['precipitation'] * 0.01
        return max(0.8, min(1.2, temp_mod * precip_mod))

    async def _update_weather(self):
        """Каждые 4 игровых месяца (8 реальных часов) обновляет погоду во всех провинциях."""
        provinces = await async_fetch_all("SELECT id FROM provinces")
        for p in provinces:
            season = random.choice(['summer', 'autumn', 'winter', 'spring'])
            temp = random.uniform(-10, 40) if season == 'winter' else random.uniform(10, 45)
            precip = random.uniform(0, 50)
            await async_execute(
                "INSERT INTO weather_log (province_id, season, temperature, precipitation) VALUES (?, ?, ?, ?)",
                (p['id'], season, temp, precip))
    
    # ================= РАЗВЕДКА =================
    async def _handle_scout(self, my_country, enemy, war, interaction):
        recon_power = my_country['info_security'] + random.randint(-10, 10)
        counter_power = enemy['counter_intelligence'] + random.randint(-5, 5)
        if counter_power <= 0:
            counter_power = 1
        success_chance = max(0.1, min(0.9, 0.5 * (recon_power / counter_power)))
        success = random.random() < success_chance

        news_channel = self.bot.get_channel(CHANNEL_IDS.get("news", 0))

        if success:
            equip_summary = await self._get_equipment_summary(enemy['id'])
            report = (
                f"🔍 Разведка {my_country['display_name'] or my_country['name']} обнаружила:\n"
                f"• Армия: {self.format_number(enemy['army_count'])} чел.\n"
                f"• Техника: {equip_summary if equip_summary else 'нет данных'}\n"
            )
            await interaction.followup.send(report, ephemeral=True)
            if news_channel:
                await news_channel.send(REPORT_TEMPLATES["scout_success"].format(
                    country=my_country['display_name'] or my_country['name']
                ))
        else:
            await interaction.followup.send("❌ Разведка провалилась – группа перехвачена.", ephemeral=True)
            if news_channel:
                await news_channel.send(REPORT_TEMPLATES["scout_fail"].format(
                    country=my_country['display_name'] or my_country['name']
                ))

        # ================= СПЕЦОПЕРАЦИИ =================
    async def _execute_specops(self, my_country, enemy, war, interaction):
        """Проводит диверсию против врага."""
        # Вероятность успеха зависит от разведки и опыта офицеров
        base_chance = 0.4
        if random.random() < base_chance:
            # Уничтожаем случайную технику или убиваем офицера
            target = random.choice(["technique", "officer"])
            if target == "technique":
                assets = await async_fetch_all(
                    "SELECT asset_name, quantity FROM military_assets WHERE country_id=? AND quantity > 0",
                    (enemy['id'],))
                if assets:
                    victim = random.choice(assets)
                    loss = min(victim['quantity'], random.randint(1, 3))
                    await async_execute("UPDATE military_assets SET quantity = quantity - ? WHERE country_id=? AND asset_name=?",
                                        (loss, enemy['id'], victim['asset_name']))
                    await interaction.followup.send(f"💥 Спецоперация успешна! Уничтожено {loss} ед. {victim['asset_name']} врага.", ephemeral=True)
                else:
                    await interaction.followup.send("⚠️ У врага нет техники для диверсии.", ephemeral=True)
            else:
                officers = await async_fetch_all("SELECT id, name FROM officers WHERE country_id=?", (enemy['id'],))
                if officers:
                    victim = random.choice(officers)
                    await async_execute("DELETE FROM officers WHERE id=?", (victim['id'],))
                    await interaction.followup.send(f"🗡️ Ликвидирован офицер {victim['name']} врага!", ephemeral=True)
                else:
                    await interaction.followup.send("⚠️ У врага нет офицеров.", ephemeral=True)
        else:
            await interaction.followup.send("❌ Спецоперация провалилась.", ephemeral=True)

    # ================= ПАРТИЗАНСКАЯ ВОЙНА =================
    async def _check_partisan_activity(self, country_id):
        """При оккупации провинций возможны восстания."""
        occupied = await async_fetch_all(
            "SELECT p.id, p.name FROM provinces p JOIN frontlines f ON p.id = f.province_id "
            "WHERE f.controlled_by_id != p.country_id AND f.war_id IN (SELECT id FROM wars WHERE status='active')"
        )
        for prov in occupied:
            if random.random() < 0.1:  # 10% шанс восстания
                # Уменьшаем армию оккупанта
                await async_execute(
                    "UPDATE countries SET army_count = army_count - ? WHERE id = (SELECT country_id FROM provinces WHERE id = ?)",
                    (random.randint(10, 100), prov['id']))
                news_channel = self.bot.get_channel(CHANNEL_IDS.get("news", 0))
                if news_channel:
                    await news_channel.send(f"🔥 В {prov['name']} вспыхнуло партизанское восстание против оккупантов!")

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

    # ================= КОМАНДА ХОДА (МОДАЛЬНОЕ ОКНО) =================
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
        app_commands.Choice(name="Снабжение/Логистика", value="supply"),
        app_commands.Choice(name="Спецоперация", value="specops"),
        app_commands.Choice(name="Тактическое отступление", value="retreat")
    ])
    @app_commands.choices(attack_type=[
        app_commands.Choice(name="Лобовая атака", value="frontal_assault"),
        app_commands.Choice(name="Фланговый манёвр", value="flanking_maneuver"),
        app_commands.Choice(name="Окружение (котёл)", value="encirclement"),
        app_commands.Choice(name="Прорыв", value="breakthrough"),
        app_commands.Choice(name="Осада", value="siege")
    ])
    async def war_action(self, interaction: discord.Interaction, action: str, attack_type: str = "frontal_assault", target_army_percent: int = 100):
        # Этот метод вызывается из модального окна (View) и не требует defer, т.к. вызывается из View.callback
        # Но чтобы он работал и как отдельная команда, делаем defer
        try:
            await interaction.response.defer(ephemeral=True)
        except:
            pass  # если уже отвечено

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

            enemy_id = war['attacker_id'] if war['defender_id'] == my_country['id'] else war['defender_id']
            enemy = await async_fetch_one("SELECT name, owner_id FROM countries WHERE id=?", (enemy_id,))

            move_num = await async_fetch_one("SELECT COUNT(*) as cnt FROM war_moves WHERE war_id=?", (war['id'],))
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

            # Проверка на немедленную симуляцию
            enemy_moves = await async_fetch_one(
                "SELECT id FROM war_moves WHERE war_id=? AND country_id=? AND created_at >= ? AND created_at < ?",
                (war['id'], enemy_id, interval_start.timestamp(), interval_start.timestamp() + 1800)
            )
            if enemy_moves:
                await self._process_round()  # запускаем обработку для всех войн (можно оптимизировать)

            # Дополнительные действия
            if action == "scout":
                await self._handle_scout(my_country, enemy, war, interaction)
            elif action == "tactics":
                tactic_name = TACTICS[attack_type]["name"]
                news_channel = self.bot.get_channel(CHANNEL_IDS.get("news", 0))
                if news_channel:
                    await news_channel.send(REPORT_TEMPLATES["tactics_change"].format(
                        country=my_country['display_name'] or my_country['name'],
                        tactic=tactic_name
                    ))

        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    # ================= ОБЪЯВЛЕНИЕ ВОЙНЫ =================
    async def _execute_war_declaration(self, interaction, attacker, defender, reason, description, is_bot=False, target_user=None):
        existing = await async_fetch_one(
            "SELECT id FROM wars WHERE ((attacker_id=? AND defender_id=?) OR (attacker_id=? AND defender_id=?)) AND status='active'",
            (attacker['id'], defender['id'], defender['id'], attacker['id'])
        )
        if existing:
            await interaction.followup.send("Вы уже воюете с этой страной.", ephemeral=True)
            return

        now = time.time()
        await async_execute(
            "INSERT INTO wars (attacker_id, defender_id, status, start_time, reason, description) VALUES (?, ?, 'active', ?, ?, ?)",
            (attacker['id'], defender['id'], now, reason, description or "")
        )

        # Инициализация линии фронта по всем провинциям участников
        provinces = await async_fetch_all(
            "SELECT id FROM provinces WHERE country_id IN (?, ?)",
            (attacker['id'], defender['id'])
        )
        for p in provinces:
            await async_execute(
                "INSERT OR IGNORE INTO frontlines (war_id, province_id, controlled_by_id, last_change) VALUES (?, ?, ?, ?)",
                (attacker['id'], p['id'], attacker['id'] if p['id'] in [x['id'] for x in await async_fetch_all("SELECT id FROM provinces WHERE country_id=?", (attacker['id'],))] else defender['id'], now)
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

        # Новость в war_reports
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
                f"**Причина:** {reason}\n"
                f"**Описание:** {description if description else 'нет'}\n\n"
                f"**Силы сторон:** {attacker_name} ({attacker['combat_capability']}) vs {defender_name} ({defender['combat_capability']})\n"
                f"**Численность:** {attacker_name} ({self.format_number(attacker['army_count'])}) vs {defender_name} ({self.format_number(defender['army_count'])})"
            )
            await channel.send(full_msg)

        # Уведомление защитнику
        if not is_bot and defender['owner_id']:
            user = self.bot.get_user(defender['owner_id'])
            if user:
                try:
                    await user.send(f"{interaction.user.mention} объявил вам войну от страны **{attacker_name}**!\nПричина: {reason}\nОписание: {description if description else 'нет'}")
                except discord.Forbidden:
                    pass

        await interaction.followup.send(f"✅ Война объявлена стране {defender_name}.", ephemeral=True)

    # ================= МИР =================
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

            if war['id'] in self.pending_peace_offers:
                await interaction.followup.send("Предложение мира уже отправлено, ожидайте ответа.", ephemeral=True)
                return

            self.pending_peace_offers[war['id']] = {"from": my_country['id'], "to": target_country['id'], "time": time.time()}

            if target_country['owner_id']:
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
            else:
                await self._bot_peace_decision(war['id'], my_country, target_country, interaction)

        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    async def _bot_peace_decision(self, war_id, my_country, target_country, interaction):
        attacker = await async_fetch_one("SELECT * FROM countries WHERE id=?", (target_country['id'],))
        my_army = my_country['army_count']
        bot_army = attacker['army_count']
        if bot_army <= 0:
            acceptance_chance = 1.0
        else:
            ratio = my_army / max(bot_army, 1)
            acceptance_chance = min(0.9, max(0.1, 0.5 + (ratio - 1) * 0.2))

        if random.random() < acceptance_chance:
            await async_execute("UPDATE wars SET status='ended' WHERE id=?", (war_id,))
            self.pending_peace_offers.pop(war_id, None)
            news_msg = WAR_PEACE_NEWS[0].format(
                country1=my_country['display_name'] or my_country['name'],
                country2=target_country['display_name'] or target_country['name']
            )
            await self._send_news(news_msg)
            await interaction.followup.send("✅ Бот принял ваше предложение мира.", ephemeral=True)
        else:
            self.pending_peace_offers.pop(war_id, None)
            await interaction.followup.send("❌ Бот отклонил предложение мира.", ephemeral=True)

    # ================= МЕТОДЫ ДЛЯ VIEW (ИЗ GAME.PY) =================
    async def _declare_war(self, interaction: discord.Interaction, attacker_id: int, defender_id: int, reason: str, description: str, is_bot: bool = False):
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
            await self._execute_war_declaration(interaction, attacker, defender, reason, description, is_bot=is_bot,
                                                target_user=None if is_bot else (await self.bot.fetch_user(defender['owner_id']) if defender['owner_id'] else None))
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    async def _declare_war_from_modal(self, interaction: discord.Interaction, attacker_id: int, defender_id: int, reason: str, description: str, is_bot: bool = False):
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
            await self._execute_war_declaration(interaction, attacker, defender, reason, description, is_bot=is_bot,
                                                target_user=None if is_bot else (await self.bot.fetch_user(defender['owner_id']) if defender['owner_id'] else None))
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    async def _make_peace(self, interaction: discord.Interaction, war_id: int):
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
            news_msg = WAR_PEACE_NEWS[0].format(country1=attacker['name'], country2=defender['name'])
            await self._send_news(news_msg)
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

    async def _notify_country_at_war(self, interaction: discord.Interaction, country_id: int):
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

    async def _send_news(self, message):
        news_channel_id = CHANNEL_IDS.get("news")
        if news_channel_id:
            channel = self.bot.get_channel(news_channel_id)
            if channel:
                await channel.send(message)

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


# ================= VIEW: ПОДТВЕРЖДЕНИЕ МИРА =================
class PeaceResponseView(discord.ui.View):
    def __init__(self, war_id, from_country_id, to_country_id, war_cog):
        super().__init__(timeout=86400)
        self.war_id = war_id
        self.from_country_id = from_country_id
        self.to_country_id = to_country_id
        self.war_cog = war_cog

    @discord.ui.button(label="Принять мир", style=discord.ButtonStyle.success)
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not country or country['id'] != self.to_country_id:
            await interaction.response.send_message("Это предложение не вам.", ephemeral=True)
            return

        await async_execute("UPDATE wars SET status='ended' WHERE id=? AND status='active'", (self.war_id,))
        self.war_cog.pending_peace_offers.pop(self.war_id, None)

        attacker = await async_fetch_one("SELECT name FROM countries WHERE id=?", (self.from_country_id,))
        defender = await async_fetch_one("SELECT name FROM countries WHERE id=?", (self.to_country_id,))
        news_msg = WAR_PEACE_NEWS[0].format(country1=attacker['name'], country2=defender['name'])
        await self.war_cog._send_news(news_msg)
        await interaction.response.edit_message(content="✅ Вы приняли мир. Война окончена.", view=None)

    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.danger)
    async def decline_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
        if not country or country['id'] != self.to_country_id:
            await interaction.response.send_message("Это предложение не вам.", ephemeral=True)
            return

        self.war_cog.pending_peace_offers.pop(self.war_id, None)
        await interaction.response.edit_message(content="Вы отклонили предложение мира.", view=None)


# ================= VIEW: ПОСЛЕВОЕННЫЕ УСЛОВИЯ =================
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

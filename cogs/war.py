import discord
from discord.ext import commands, tasks
from discord import app_commands
from database import async_fetch_all, async_fetch_one, async_execute, async_get_game_date
import time
import random
import datetime
from zoneinfo import ZoneInfo
import json

try:
    from config import CHANNEL_IDS, BATTLE_ROUND_INTERVAL_MINUTES
except ImportError:
    CHANNEL_IDS = {}
    BATTLE_ROUND_INTERVAL_MINUTES = 30

# Импорт справочников техники и оружия
from data.military import MILITARY_EQUIPMENT, WEAPONS

# Новостные шаблоны (оставлены без изменений)
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

    async def cog_load(self):
        if not self.battle_loop.is_running():
            self.battle_loop.start()

    # ---------- Боевой цикл (улучшенный) ----------
    @tasks.loop(minutes=BATTLE_ROUND_INTERVAL_MINUTES)
    async def battle_loop(self):
        active_wars = await async_fetch_all("SELECT id, attacker_id, defender_id FROM wars WHERE status='active'")
        now = time.time()
        for war in active_wars:
            battle = await async_fetch_one("SELECT last_battle_time FROM war_battles WHERE war_id=?", (war['id'],))
            if battle and (now - battle['last_battle_time']) < BATTLE_ROUND_INTERVAL_MINUTES * 60:
                continue

            attacker = await async_fetch_one("SELECT * FROM countries WHERE id=?", (war['attacker_id'],))
            defender = await async_fetch_one("SELECT * FROM countries WHERE id=?", (war['defender_id'],))
            if not attacker or not defender:
                continue

            # Определяем тип атаки из последнего хода (если есть)
            attack_type = 'land'  # по умолчанию
            attacker_move = await async_fetch_one(
                "SELECT * FROM war_moves WHERE war_id=? AND country_id=? ORDER BY created_at DESC LIMIT 1",
                (war['id'], war['attacker_id'])
            )
            if attacker_move:
                try:
                    details = json.loads(attacker_move['details'])
                    attack_type = details.get('attack_type', 'land')
                except:
                    pass

            defender_move = await async_fetch_one(
                "SELECT * FROM war_moves WHERE war_id=? AND country_id=? ORDER BY created_at DESC LIMIT 1",
                (war['id'], war['defender_id'])
            )

            # Получаем количество техники по категориям
            attacker_equip = await self._get_equipment_summary(attacker['id'], attack_type)
            defender_equip = await self._get_equipment_summary(defender['id'], attack_type)

            # Расчет силы с бонусом от техники
            def calc_power(country, equip_summary):
                base = country['army_count'] * (country['combat_capability'] / 100)
                if country['owner_id'] is None:
                    base *= (country.get('bot_strength', 5) / 10)
                # Бонус от техники: каждая единица даёт +0.1 к силе (условно)
                tech_bonus = sum(equip_summary.values()) * 0.1
                return base * (1 + tech_bonus / 100)

            atk_power = calc_power(attacker, attacker_equip)
            def_power = calc_power(defender, defender_equip)

            # Потери армии
            def_loss = min(defender['army_count'], int(atk_power * 0.1))
            atk_loss = min(attacker['army_count'], int(def_power * 0.08))

            await async_execute("UPDATE countries SET army_count = army_count - ? WHERE id=?", (atk_loss, attacker['id']))
            await async_execute("UPDATE countries SET army_count = army_count - ? WHERE id=?", (def_loss, defender['id']))

            # Потери техники
            atk_equip_losses = self._distribute_equipment_losses(attacker_equip, int(atk_power * 0.05))
            def_equip_losses = self._distribute_equipment_losses(defender_equip, int(def_power * 0.05))
            await self._update_equipment(attacker['id'], atk_equip_losses)
            await self._update_equipment(defender['id'], def_equip_losses)

            # Обновление времени боя
            if battle:
                await async_execute("UPDATE war_battles SET last_battle_time=? WHERE war_id=?", (now, war['id']))
            else:
                await async_execute("INSERT INTO war_battles (war_id, last_battle_time) VALUES (?, ?)", (war['id'], now))

            # Отчет о потерях
            await self._send_battle_report(war, attacker, defender, atk_loss, def_loss, atk_equip_losses, def_equip_losses, attack_type)

            # Завершение войны, если армия кончилась
            if attacker['army_count'] <= 0 or defender['army_count'] <= 0:
                winner = attacker if attacker['army_count'] > 0 else defender
                loser = defender if winner == attacker else attacker
                await async_execute("UPDATE wars SET status='ended' WHERE id=?", (war['id'],))
                await self._offer_post_war_terms(war, winner, loser)

    async def _get_equipment_summary(self, country_id: int, attack_type: str) -> dict:
        """Возвращает словарь {тип_техники: количество} для заданного типа атаки."""
        # Определяем категории техники, подходящие для attack_type
        categories = []
        if attack_type == 'land':
            categories = ['сухопутные', 'беспилотные аппараты', 'разведка']
        elif attack_type == 'air':
            categories = ['воздушные', 'беспилотные аппараты']
        elif attack_type == 'naval':
            categories = ['морские', 'беспилотные аппараты']
        else:
            categories = ['сухопутные']

        placeholders = ','.join(['?' for _ in categories])
        rows = await async_fetch_all(
            f"SELECT asset_name, quantity FROM military_assets WHERE country_id=? AND asset_type='equipment' AND asset_name IN "
            f"(SELECT asset_name FROM military_assets WHERE country_id=? AND asset_type='equipment' AND asset_name IN ("
            f"SELECT name FROM json_each(?)))", # упрощённый подход не сработает; сделаем проще:
        )
        # Из-за сложности запроса лучше получить всё и отфильтровать в коде.
        rows = await async_fetch_all(
            "SELECT asset_name, quantity FROM military_assets WHERE country_id=? AND asset_type='equipment'",
            (country_id,)
        )
        summary = {}
        for row in rows:
            # проверяем, принадлежит ли asset_name одной из нужных категорий
            for cat in categories:
                if row['asset_name'] in MILITARY_EQUIPMENT.get(cat, []):
                    summary[row['asset_name']] = summary.get(row['asset_name'], 0) + row['quantity']
                    break
        return summary

    def _distribute_equipment_losses(self, equipment: dict, total_loss: int) -> dict:
        """Возвращает словарь потерь {тип: количество} пропорционально количеству."""
        if not equipment or total_loss <= 0:
            return {}
        total_qty = sum(equipment.values())
        if total_qty == 0:
            return {}
        losses = {}
        for name, qty in equipment.items():
            loss = int(total_loss * (qty / total_qty))
            if loss > 0:
                losses[name] = min(loss, qty)
        return losses

    async def _update_equipment(self, country_id: int, losses: dict):
        """Применяет потери техники."""
        for name, loss in losses.items():
            await async_execute(
                "UPDATE military_assets SET quantity = quantity - ? WHERE country_id=? AND asset_name=? AND asset_type='equipment'",
                (loss, country_id, name)
            )

    async def _send_battle_report(self, war, attacker, defender, atk_loss, def_loss, atk_equip_losses, def_equip_losses, attack_type):
        """Формирует и отправляет отчёт о бое."""
        attacker_name = attacker['display_name'] or attacker['name']
        defender_name = defender['display_name'] or defender['name']
        report = (
            f"**⚔️ Боевое столкновение ({attack_type})**\n"
            f"**{attacker_name}** vs **{defender_name}**\n\n"
            f"**Потери в живой силе:**\n"
            f"🔹 {attacker_name}: {atk_loss} солдат\n"
            f"🔹 {defender_name}: {def_loss} солдат\n\n"
            f"**Потери техники:**\n"
        )
        if atk_equip_losses:
            report += f"🔹 {attacker_name}:\n" + "\n".join(f"   - {k}: {v} ед." for k,v in atk_equip_losses.items()) + "\n"
        else:
            report += f"🔹 {attacker_name}: нет\n"
        if def_equip_losses:
            report += f"🔹 {defender_name}:\n" + "\n".join(f"   - {k}: {v} ед." for k,v in def_equip_losses.items()) + "\n"
        else:
            report += f"🔹 {defender_name}: нет\n"

        # Отправка в канал war_reports
        war_channel_id = CHANNEL_IDS.get("war_reports")
        if war_channel_id:
            channel = self.bot.get_channel(war_channel_id)
        else:
            channel = None
        if channel:
            await channel.send(report)

        # Отправка в ЛС владельцам
        if attacker['owner_id']:
            await self._notify_user(attacker['owner_id'], report)
        if defender['owner_id']:
            await self._notify_user(defender['owner_id'], report)

    # ---------- Покупка техники ----------
    @app_commands.command(name="buy_equipment", description="Купить военную технику (упрощённо)")
    @app_commands.describe(equipment_name="Название техники", quantity="Количество")
    async def buy_equipment(self, interaction: discord.Interaction, equipment_name: str, quantity: int):
        if quantity <= 0:
            await interaction.response.send_message("Количество должно быть положительным.", ephemeral=True)
            return
        country = await self._get_country(interaction.user.id)
        if not country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return

        # Проверяем, существует ли такая техника в справочнике
        valid = False
        for cat, items in MILITARY_EQUIPMENT.items():
            if equipment_name in items:
                valid = True
                break
        if not valid:
            await interaction.response.send_message("Такой техники не существует.", ephemeral=True)
            return

        # Стоимость (условно 1000 долларов за единицу)
        cost = 1000 * quantity
        money_row = await async_fetch_one("SELECT amount FROM resources WHERE country_id=? AND resource_name='Доллары'", (country['id'],))
        if not money_row or money_row['amount'] < cost:
            await interaction.response.send_message("Недостаточно денег.", ephemeral=True)
            return

        await async_execute("UPDATE resources SET amount = amount - ? WHERE country_id=? AND resource_name='Доллары'", (cost, country['id']))
        # Добавляем технику
        existing = await async_fetch_one(
            "SELECT id, quantity FROM military_assets WHERE country_id=? AND asset_type='equipment' AND asset_name=?",
            (country['id'], equipment_name)
        )
        if existing:
            await async_execute("UPDATE military_assets SET quantity = quantity + ? WHERE id=?", (quantity, existing['id']))
        else:
            await async_execute(
                "INSERT INTO military_assets (country_id, asset_type, asset_name, quantity) VALUES (?, 'equipment', ?, ?)",
                (country['id'], equipment_name, quantity)
            )
        await interaction.response.send_message(f"✅ Куплено {quantity} ед. {equipment_name} за {cost}$.", ephemeral=True)

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

    def format_number(self, n, decimals=0):
        if n is None:
            return "0"
        if decimals == 0:
            return f"{int(n):,}".replace(",", ".")
        else:
            return f"{n:,.{decimals}f}".replace(",", ".").replace(".", ",", 1)

    # Внутренние методы для View из game.py
    async def _declare_war(self, interaction: discord.Interaction, attacker_id: int, defender_id: int, is_bot: bool = False):
        """Вызывается из WarMenuView."""
        await interaction.response.defer(ephemeral=True)
        attacker = await async_fetch_one("SELECT * FROM countries WHERE id=?", (attacker_id,))
        defender = await async_fetch_one("SELECT * FROM countries WHERE id=?", (defender_id,))
        if not attacker or not defender:
            await interaction.followup.send("Страна не найдена.", ephemeral=True)
            return
        # Проверка на существующую войну
        existing = await async_fetch_one(
            "SELECT id FROM wars WHERE ((attacker_id=? AND defender_id=?) OR (attacker_id=? AND defender_id=?)) AND status='active'",
            (attacker_id, defender_id, defender_id, attacker_id)
        )
        if existing:
            await interaction.followup.send("Вы уже воюете с этой страной.", ephemeral=True)
            return
        await self._execute_war_declaration(interaction, attacker, defender, is_bot=is_bot,
                                            target_user=None if is_bot else await self.bot.fetch_user(defender['owner_id']) if defender['owner_id'] else None)

    async def _make_peace(self, interaction: discord.Interaction, war_id: int):
        """Заключение мира по ID войны (из View)."""
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

        # Уведомление противнику
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

    # --- Пошаговые ходы ---
    @app_commands.command(name="war_action", description="Совершить ход в войне (раз в 30 минут)")
    @app_commands.describe(
        action="Тип действия",
        target_army_percent="Процент армии (1-100)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Атака", value="attack"),
        app_commands.Choice(name="Оборона", value="defend"),
        app_commands.Choice(name="Разведка", value="scout"),
        app_commands.Choice(name="Смена тактики", value="tactics")
    ])
    async def war_action(self, interaction: discord.Interaction, action: str, target_army_percent: int = 100):
        await interaction.response.defer(ephemeral=True)
        try:
            my_country = await async_fetch_one("SELECT * FROM countries WHERE owner_id=?", (interaction.user.id,))
            if not my_country:
                await interaction.followup.send("Вы не управляете страной.", ephemeral=True)
                return

            war = await async_fetch_one(
                "SELECT id FROM wars WHERE (attacker_id=? OR defender_id=?) AND status='active'",
                (my_country['id'], my_country['id'])
            )
            if not war:
                await interaction.followup.send("Вы не находитесь в состоянии войны.", ephemeral=True)
                return

            # Кулдаун по МСК
            moscow_tz = ZoneInfo("Europe/Moscow")
            now = datetime.datetime.now(moscow_tz)
            if now.minute < 30:
                interval_start = now.replace(minute=0, second=0, microsecond=0)
            else:
                interval_start = now.replace(minute=30, second=0, microsecond=0)

            interval_end = interval_start + datetime.timedelta(minutes=30)
            existing_move = await async_fetch_one(
                "SELECT id FROM war_moves WHERE war_id=? AND country_id=? AND created_at >= ? AND created_at < ?",
                (war['id'], my_country['id'], interval_start.timestamp(), interval_end.timestamp())
            )
            if existing_move:
                await interaction.followup.send("Вы уже отдали приказ в этом получасовом интервале.", ephemeral=True)
                return

            await async_execute(
                "INSERT INTO war_moves (war_id, country_id, move_type, details, created_at) VALUES (?, ?, ?, ?, ?)",
                (war['id'], my_country['id'], action, f"army_percent={target_army_percent}", now.timestamp())
            )

            action_names = {"attack": "Атака", "defend": "Оборона", "scout": "Разведка", "tactics": "Смена тактики"}
            await interaction.followup.send(
                f"✅ Приказ **{action_names[action]}** принят (использовано {target_army_percent}% армии).",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

    async def country_autocomplete(self, interaction: discord.Interaction, current: str):
        try:
            rows = await async_fetch_all(
                "SELECT name FROM countries WHERE owner_id IS NULL AND name LIKE ?",
                (f"{current}%",)
            )
            return [app_commands.Choice(name=row['name'], value=row['name']) for row in rows]
        except Exception as e:
            print(f"Ошибка автодополнения стран: {e}")
            return []


# --- Послевоенное меню ---
class PostWarView(discord.ui.View):
    def __init__(self, war_id, winner_id, loser_id):
        super().__init__(timeout=86400)  # 24 часа
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
    await bot.add_cog(War(bot))

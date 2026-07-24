import discord
from discord.ext import commands, tasks
from discord import app_commands
from database import async_fetch_all, async_fetch_one, async_execute, async_get_game_date
import time
import random
import datetime
from zoneinfo import ZoneInfo

try:
    from config import BATTLE_ROUND_INTERVAL_MINUTES
except ImportError:
    BATTLE_ROUND_INTERVAL_MINUTES = 30
try:
    from config import CHANNEL_IDS
except ImportError:
    CHANNEL_IDS = {}

# Новостные шаблоны для войны (можно скопировать из game.py или оставить здесь)
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
        """Запускается при загрузке кога."""
        if not self.battle_loop.is_running():
            self.battle_loop.start()

    @tasks.loop(minutes=30)  # можно взять из конфига
    async def battle_loop(self):
        """Боевой цикл – выполняется каждые 30 минут."""
        active_wars = await async_fetch_all("SELECT id, attacker_id, defender_id FROM wars WHERE status='active'")
        now = time.time()
        for war in active_wars:
            battle = await async_fetch_one("SELECT last_battle_time FROM war_battles WHERE war_id=?", (war['id'],))
            if battle and (now - battle['last_battle_time']) < 30 * 60:  # 30 минут
                continue

            attacker = await async_fetch_one("SELECT * FROM countries WHERE id=?", (war['attacker_id'],))
            defender = await async_fetch_one("SELECT * FROM countries WHERE id=?", (war['defender_id'],))
            if not attacker or not defender:
                continue

            # Расчёт потерь с учётом bot_strength
            if attacker['owner_id'] is None:
                bot_factor = (attacker.get('bot_strength', 5) / 10)
            else:
                bot_factor = 1.0
            atk_power = attacker['army_count'] * (attacker['combat_capability'] / 100) * bot_factor

            if defender['owner_id'] is None:
                bot_factor = (defender.get('bot_strength', 5) / 10)
            else:
                bot_factor = 1.0
            def_power = defender['army_count'] * (defender['combat_capability'] / 100) * bot_factor

            def_loss = min(defender['army_count'], int(atk_power * 0.1))
            atk_loss = min(attacker['army_count'], int(def_power * 0.08))

            await async_execute("UPDATE countries SET army_count = army_count - ? WHERE id=?", (atk_loss, attacker['id']))
            await async_execute("UPDATE countries SET army_count = army_count - ? WHERE id=?", (def_loss, defender['id']))

            if battle:
                await async_execute("UPDATE war_battles SET last_battle_time=? WHERE war_id=?", (now, war['id']))
            else:
                await async_execute("INSERT INTO war_battles (war_id, last_battle_time) VALUES (?, ?)", (war['id'], now))

            # Проверка на завершение войны
            if attacker['army_count'] <= 0 or defender['army_count'] <= 0:
                winner = attacker if attacker['army_count'] > 0 else defender
                loser = defender if winner == attacker else attacker
                await async_execute("UPDATE wars SET status='ended' WHERE id=?", (war['id'],))
                # Отправить новость о победе
                # ... (можно добавить аналогично как при объявлении)
                # Предложить победителю условия
                await self._offer_post_war_terms(war, winner, loser)
        # Боевой цикл будет запущен в main.py после загрузки кога

        async def _declare_war(self, interaction: discord.Interaction, attacker_id: int, defender_id: int, is_bot: bool = False):
        """Внутренний метод для объявления войны, вызывается из View."""
        await interaction.response.defer(ephemeral=True)
        try:
            # Проверки
            existing = await async_fetch_one(
                "SELECT id FROM wars WHERE ((attacker_id=? AND defender_id=?) OR (attacker_id=? AND defender_id=?)) AND status='active'",
                (attacker_id, defender_id, defender_id, attacker_id)
            )
            if existing:
                await interaction.followup.send("Вы уже воюете с этой страной.", ephemeral=True)
                return

            now = time.time()
            await async_execute(
                "INSERT INTO wars (attacker_id, defender_id, status, start_time) VALUES (?, ?, 'active', ?)",
                (attacker_id, defender_id, now)
            )

            attacker = await async_fetch_one("SELECT * FROM countries WHERE id=?", (attacker_id,))
            defender = await async_fetch_one("SELECT * FROM countries WHERE id=?", (defender_id,))
            if not attacker or not defender:
                await interaction.followup.send("Страна не найдена.", ephemeral=True)
                return

            # Новость
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

            # Уведомление игроку-защитнику
            if not is_bot and defender['owner_id']:
                target_user = self.bot.get_user(defender['owner_id'])
                if target_user:
                    try:
                        await target_user.send(
                            f"{interaction.user.mention} объявил вам войну от страны **{attacker_name}**!"
                        )
                    except discord.Forbidden:
                        pass

            await interaction.followup.send(f"Война объявлена стране {defender_name}.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка при объявлении войны: {e}", ephemeral=True)

    async def _make_peace(self, interaction: discord.Interaction, war_id: int):
        """Заключение мира по ID войны."""
        await interaction.response.defer(ephemeral=True)
        try:
            war = await async_fetch_one("SELECT * FROM wars WHERE id=? AND status='active'", (war_id,))
            if not war:
                await interaction.followup.send("Война не найдена или уже завершена.", ephemeral=True)
                return
            my_country = await async_fetch_one("SELECT id FROM countries WHERE owner_id=?", (interaction.user.id,))
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
                        await target_user.send(
                            f"{interaction.user.mention} предложил мир от страны **{my_country['name']}**. Война окончена."
                        )
                    except discord.Forbidden:
                        pass

            await interaction.followup.send("Мир заключён.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка: {e}", ephemeral=True)

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

    # -------------------------------------------------
    # Команды
    # -------------------------------------------------
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

            existing = await async_fetch_one(
                "SELECT id FROM wars WHERE ((attacker_id=? AND defender_id=?) OR (attacker_id=? AND defender_id=?)) AND status='active'",
                (my_country['id'], target_country['id'], target_country['id'], my_country['id'])
            )
            if existing:
                await interaction.followup.send("Вы уже воюете с этой страной.", ephemeral=True)
                return

            now = time.time()
            await async_execute(
                "INSERT INTO wars (attacker_id, defender_id, status, start_time) VALUES (?, ?, 'active', ?)",
                (my_country['id'], target_country['id'], now)
            )

            # Новость в war_reports
            attacker_name = my_country['display_name'] or my_country['name']
            defender_name = target_country['display_name'] or target_country['name']
            attacker_ruler = my_country['ruler_name'] or "Неизвестный правитель"
            defender_ruler = target_country['ruler_name'] or "Неизвестный правитель"
            attacker_army = my_country['army_count']
            defender_army = target_country['army_count']
            attacker_strength = my_country['combat_capability']
            defender_strength = target_country['combat_capability']

            game_date = await async_get_game_date()
            date_str = game_date.strftime("%d.%m.%Y")
            news_template = random.choice(WAR_START_NEWS)
            news_msg = news_template.format(
                attacker=attacker_name, attacker_ruler=attacker_ruler,
                defender=defender_name, defender_ruler=defender_ruler
            )

            war_channel_id = CHANNEL_IDS.get("war_reports")
            if war_channel_id:
                channel = self.bot.get_channel(war_channel_id)
            else:
                channel = await self._get_channel_or_create(interaction.guild, "военные-сводки")
            if channel:
                full_msg = (
                    f"# ⚔️ Объявление войны\n\n"
                    f"{news_msg}\n\n"
                    f"**Дата:** {date_str}\n"
                    f"**Силы сторон:** {attacker_name} ({attacker_strength}) vs {defender_name} ({defender_strength})\n"
                    f"**Численность:** {attacker_name} ({self.format_number(attacker_army)}) vs {defender_name} ({self.format_number(defender_army)})"
                )
                await channel.send(full_msg)

            try:
                await target.send(f"{interaction.user.mention} объявил вам войну от страны **{attacker_name}**!")
            except discord.Forbidden:
                pass

            await interaction.followup.send(f"Война объявлена стране {defender_name}.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка при объявлении войны: {e}", ephemeral=True)

    @app_commands.command(name="declare_war_bot", description="Объявить войну свободной стране (бот)")
    @app_commands.autocomplete(country=country_autocomplete)
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

            existing = await async_fetch_one(
                "SELECT id FROM wars WHERE ((attacker_id=? AND defender_id=?) OR (attacker_id=? AND defender_id=?)) AND status='active'",
                (my_country['id'], target_country['id'], target_country['id'], my_country['id'])
            )
            if existing:
                await interaction.followup.send("Вы уже воюете с этой страной.", ephemeral=True)
                return

            now = time.time()
            await async_execute(
                "INSERT INTO wars (attacker_id, defender_id, status, start_time) VALUES (?, ?, 'active', ?)",
                (my_country['id'], target_country['id'], now)
            )

            attacker_name = my_country['display_name'] or my_country['name']
            defender_name = target_country['display_name'] or target_country['name']
            attacker_ruler = my_country['ruler_name'] or "Неизвестный правитель"
            defender_ruler = "Неизвестный правитель"
            attacker_army = my_country['army_count']
            defender_army = target_country['army_count']
            attacker_strength = my_country['combat_capability']
            defender_strength = target_country['combat_capability']

            game_date = await async_get_game_date()
            date_str = game_date.strftime("%d.%m.%Y")
            news_template = random.choice(WAR_START_NEWS)
            news_msg = news_template.format(
                attacker=attacker_name, attacker_ruler=attacker_ruler,
                defender=defender_name, defender_ruler=defender_ruler
            )

            war_channel_id = CHANNEL_IDS.get("war_reports")
            if war_channel_id:
                channel = self.bot.get_channel(war_channel_id)
            else:
                channel = await self._get_channel_or_create(interaction.guild, "военные-сводки")
            if channel:
                full_msg = (
                    f"# ⚔️ Объявление войны\n\n"
                    f"{news_msg}\n\n"
                    f"**Дата:** {date_str}\n"
                    f"**Силы сторон:** {attacker_name} ({attacker_strength}) vs {defender_name} ({defender_strength})\n"
                    f"**Численность:** {attacker_name} ({self.format_number(attacker_army)}) vs {defender_name} ({self.format_number(defender_army)})"
                )
                await channel.send(full_msg)

            await interaction.followup.send(f"Война объявлена стране {defender_name}.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка при объявлении войны: {e}", ephemeral=True)

    @app_commands.command(name="peace_treaty", description="Предложить мир противнику")
    async def peace_treaty(self, interaction: discord.Interaction, target: discord.Member):
        if target.id == interaction.user.id:
            await interaction.response.send_message("Нельзя заключить мир с самим собой.", ephemeral=True)
            return
        my_country = await self._get_country(interaction.user.id)
        if not my_country:
            await interaction.response.send_message("Вы не управляете страной.", ephemeral=True)
            return
        target_country = await self._get_country(target.id)
        if not target_country:
            await interaction.response.send_message("Этот игрок не управляет страной.", ephemeral=True)
            return
        war = await async_fetch_one(
            "SELECT id FROM wars WHERE ((attacker_id=? AND defender_id=?) OR (attacker_id=? AND defender_id=?)) AND status='active'",
            (my_country['id'], target_country['id'], target_country['id'], my_country['id'])
        )
        if not war:
            await interaction.response.send_message("Вы не находитесь в состоянии войны с этой страной.", ephemeral=True)
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
        await interaction.response.send_message(f"Мир заключён с {target_country['name']}.", ephemeral=True)

    # -------------------------------------------------
    # Боевой цикл (временная заглушка, будет заменена на пошаговый)
    # -------------------------------------------------
    async def battle_tick(self):
        """Выполняется каждые 30 минут (или согласно конфигу). Пока работает старая механика."""
        active_wars = await async_fetch_all("SELECT id, attacker_id, defender_id FROM wars WHERE status='active'")
        now = time.time()
        for war in active_wars:
            # Существующая логика боя (перенесена из main.py)
            battle = await async_fetch_one("SELECT last_battle_time FROM war_battles WHERE war_id=?", (war['id'],))
            if battle and (now - battle['last_battle_time']) < BATTLE_ROUND_INTERVAL_MINUTES * 60:
                continue
            attacker = await async_fetch_one("SELECT * FROM countries WHERE id=?", (war['attacker_id'],))
            defender = await async_fetch_one("SELECT * FROM countries WHERE id=?", (war['defender_id'],))
            if not attacker or not defender:
                continue
            # Учёт силы бота для стран, не управляемых игроком
            if attacker['owner_id'] is None:
                bot_factor = (attacker.get('bot_strength', 5) / 10)
            else:
                bot_factor = 1.0
            atk_power = attacker['army_count'] * (attacker['combat_capability'] / 100) * bot_factor
            
            if defender['owner_id'] is None:
                bot_factor = (defender.get('bot_strength', 5) / 10)
            else:
                bot_factor = 1.0
            def_power = defender['army_count'] * (defender['combat_capability'] / 100) * bot_factor
            def_loss = min(defender['army_count'], int(atk_power * 0.1))
            atk_loss = min(attacker['army_count'], int(def_power * 0.08))
            await async_execute("UPDATE countries SET army_count = army_count - ? WHERE id=?", (atk_loss, attacker['id']))
            await async_execute("UPDATE countries SET army_count = army_count - ? WHERE id=?", (def_loss, defender['id']))
            if battle:
                await async_execute("UPDATE war_battles SET last_battle_time=? WHERE war_id=?", (now, war['id']))
            else:
                await async_execute("INSERT INTO war_battles (war_id, last_battle_time) VALUES (?, ?)", (war['id'], now))
            if attacker['army_count'] <= 0 or defender['army_count'] <= 0:
                await async_execute("UPDATE wars SET status='ended' WHERE id=?", (war['id'],))
                # TODO: отправить сообщение о завершении войны

    # -------------------------------------------------
    # СЛУЖЕБНЫЕ МЕТОДЫ
    # -------------------------------------------------
    async def _offer_post_war_terms(self, war, winner, loser):
        """Отправляет победителю меню с условиями."""
        if winner['owner_id'] is None:
            return  # бот не выбирает
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
    
    async def country_autocomplete(self, interaction: discord.Interaction, current: str):
        """Автодополнение для declare_war_bot (будет перенесено из game.py)"""
        try:
            rows = await async_fetch_all(
                "SELECT name FROM countries WHERE owner_id IS NULL AND name LIKE ?",
                (f"{current}%",)
            )
            return [app_commands.Choice(name=row['name'], value=row['name']) for row in rows]
        except Exception as e:
            print(f"Ошибка автодополнения стран: {e}")
            return []

class PostWarView(discord.ui.View):
    def __init__(self, war_id, winner_id, loser_id):
        super().__init__(timeout=86400)  # 24 часа на выбор
        self.war_id = war_id
        self.winner_id = winner_id
        self.loser_id = loser_id

    @discord.ui.button(label="Аннексировать полностью", style=discord.ButtonStyle.danger)
    async def annex_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Перенести все регионы (провинции) победителю
        await async_execute("UPDATE provinces SET country_id = ? WHERE country_id = ?", (self.winner_id, self.loser_id))
        # Удалить проигравшую страну (у неё больше не будет owner_id)
        await async_execute("DELETE FROM countries WHERE id = ?", (self.loser_id,))
        # Закрыть войну
        await async_execute("DELETE FROM wars WHERE id = ?", (self.war_id,))
        await interaction.response.edit_message(content="✅ Страна полностью аннексирована. Территория перешла к вам.", view=None)

    @discord.ui.button(label="Забрать определённые регионы", style=discord.ButtonStyle.primary)
    async def take_regions_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Здесь в будущем откроем выбор регионов
        await interaction.response.send_message("⚠️ Выбор регионов появится позже.", ephemeral=True)

    @discord.ui.button(label="Сделать марионеткой", style=discord.ButtonStyle.success)
    async def puppet_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Установить зависимость
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

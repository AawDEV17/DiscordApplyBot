import discord
from discord.ext import commands
import re
TOKEN = "MTM1NzczODQ4MDcxMjgxNDU5Mg.GS4V-r.zaZ5bwUMTFjXbMJxompE_QfffB4RfWJqXUm3Tk" 

CURATOR_ROLE_ID = 1357739823896461472
YOUR_GUILD_ID = 1349333696754487296
MODERATOR_ROLE_ID = 1357753727372628324

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

class ApplicationModal(discord.ui.Modal, title="Заявка на модератора"):
    nickname = discord.ui.TextInput(label="Ваш никнейм", placeholder="Только англ. буквы и цифры", required=True, max_length=16)
    age = discord.ui.TextInput(label="Ваш возраст", placeholder="Только цифры", required=True, max_length=2)
    experience = discord.ui.TextInput(label="Опыт модерации", required=True)
    online_time = discord.ui.TextInput(label="Часы активности в день", required=True)
    reason = discord.ui.TextInput(label="Почему вы хотите стать модератором?", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        if not re.fullmatch(r"^[a-zA-Z0-9]+$", self.nickname.value):
            await interaction.response.send_message("❌ Ник должен содержать только английские буквы и цифры!", ephemeral=True)
            return
        if not self.age.value.isdigit():
            await interaction.response.send_message("❌ В возрасте можно использовать только цифры!", ephemeral=True)
            return

        embed = discord.Embed(title="📩 Новая заявка", color=discord.Color.blue())
        embed.add_field(name="👤 Ник", value=self.nickname.value, inline=False)
        embed.add_field(name="📅 Возраст", value=self.age.value, inline=False)
        embed.add_field(name="🔧 Опыт", value=self.experience.value, inline=False)
        embed.add_field(name="🕒 Часы онлайн", value=self.online_time.value, inline=False)
        embed.add_field(name="📝 Причина", value=self.reason.value, inline=False)
        embed.set_footer(text=f"Отправитель: {interaction.user}", icon_url=interaction.user.display_avatar.url)

        guild = bot.get_guild(YOUR_GUILD_ID)
        curators = [m for m in guild.members if CURATOR_ROLE_ID in [r.id for r in m.roles]]

        for curator in curators:
            try:
                await curator.send(embed=embed, view=ReviewView(interaction.user.id, embed))
            except:
                print(f"❌ Не удалось отправить ЛС {curator}")

        await interaction.response.send_message("✅ Ваша заявка отправлена на рассмотрение.", ephemeral=True)

class ReviewView(discord.ui.View):
    def __init__(self, applicant_id, embed):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id
        self.original_embed = embed

    async def get_curator(self, interaction):
        guild = bot.get_guild(YOUR_GUILD_ID)
        member = guild.get_member(interaction.user.id)
        if member and CURATOR_ROLE_ID in [role.id for role in member.roles]:
            return True
        await interaction.response.send_message("❌ У вас нет прав", ephemeral=True)
        return False

    @discord.ui.button(label="👀 Рассмотреть", style=discord.ButtonStyle.secondary)
    async def review(self, interaction: discord.Interaction, _):
        if not await self.get_curator(interaction): return
        user = await bot.fetch_user(self.applicant_id)
        await user.send(f"🔍 Ваша заявка на рассмотрении куратором **{interaction.user}**.")
        await interaction.response.send_message("✅ Участник уведомлён.", ephemeral=True)

    @discord.ui.button(label="✅ Принять", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, _):
        if not await self.get_curator(interaction): return
        guild = bot.get_guild(YOUR_GUILD_ID)
        user = guild.get_member(self.applicant_id)
        if user:
            role = guild.get_role(MODERATOR_ROLE_ID)
            await user.add_roles(role)
            await user.send("🎉 Ваша заявка была **принята**. Добро пожаловать в команду!")
        await interaction.message.edit(content="✅ Заявка принята!", view=None)

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, _):
        if not await self.get_curator(interaction): return
        user = await bot.fetch_user(self.applicant_id)
        await user.send("❌ Ваша заявка была **отклонена**.")
        await interaction.message.edit(content="❌ Заявка отклонена!", view=None)

    @discord.ui.button(label="💬 Связаться", style=discord.ButtonStyle.primary)
    async def contact(self, interaction: discord.Interaction, _):
        if not await self.get_curator(interaction): return
        await interaction.response.send_message("✉️ Введите сообщение для участника.", ephemeral=True)

        def check(msg):
            return msg.author == interaction.user and isinstance(msg.channel, discord.DMChannel)

        msg = await bot.wait_for("message", check=check)
        user = await bot.fetch_user(self.applicant_id)

        embed = discord.Embed(title="📨 Сообщение от куратора", description=msg.content, color=discord.Color.orange())
        await user.send(embed=embed, view=ChatView(interaction.user.id, self.applicant_id, self.original_embed))
        await interaction.followup.send("✅ Сообщение отправлено участнику.", ephemeral=True)

class ChatView(discord.ui.View):
    def __init__(self, curator_id, user_id, embed):
        super().__init__(timeout=None)
        self.curator_id = curator_id
        self.user_id = user_id
        self.original_embed = embed

    @discord.ui.button(label="💬 Ответить", style=discord.ButtonStyle.primary)
    async def reply(self, interaction: discord.Interaction, _):
        await interaction.response.send_message("✍️ Напишите ваш ответ.", ephemeral=True)

        def check(msg):
            return msg.author.id == interaction.user.id and isinstance(msg.channel, discord.DMChannel)

        msg = await bot.wait_for("message", check=check)
        other_user_id = self.curator_id if interaction.user.id == self.user_id else self.user_id
        other_user = await bot.fetch_user(other_user_id)

        title = "📩 Ответ от куратора" if interaction.user.id == self.curator_id else "📩 Ответ от участника"
        color = discord.Color.green() if interaction.user.id == self.user_id else discord.Color.blue()
        embed = discord.Embed(title=title, description=msg.content, color=color)

        await other_user.send(embed=embed, view=ChatView(self.curator_id, self.user_id, self.original_embed))
        await interaction.followup.send("✅ Ответ отправлен.", ephemeral=True)

    @discord.ui.button(label="🔒 Завершить связь", style=discord.ButtonStyle.danger)
    async def end(self, interaction: discord.Interaction, _):
        other_user_id = self.curator_id if interaction.user.id == self.user_id else self.user_id
        other_user = await bot.fetch_user(other_user_id)
        await other_user.send("🔒 Связь завершена.")
        await interaction.response.send_message("✅ Вы завершили диалог.", ephemeral=True)

        # Повторно отправить куратору заявку с двумя кнопками
        guild = bot.get_guild(YOUR_GUILD_ID)
        curators = [m for m in guild.members if CURATOR_ROLE_ID in [r.id for r in m.roles]]
        view = FinalDecisionView(self.user_id)
        for curator in curators:
            try:
                await curator.send("🔁 Заявка снова доступна для рассмотрения.", embed=self.original_embed, view=view)
            except:
                print(f"❌ Ошибка отправки финального обзора {curator}")

class FinalDecisionView(discord.ui.View):
    def __init__(self, applicant_id):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id

    @discord.ui.button(label="✅ Принять", style=discord.ButtonStyle.success)
    async def accept_final(self, interaction: discord.Interaction, _):
        guild = bot.get_guild(YOUR_GUILD_ID)
        user = guild.get_member(self.applicant_id)
        if user:
            role = guild.get_role(MODERATOR_ROLE_ID)
            await user.add_roles(role)
            await user.send("🎉 Ваша заявка была **принята**. Добро пожаловать в команду!")
        await interaction.message.edit(content="✅ Заявка принята!", view=None)

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.danger)
    async def decline_final(self, interaction: discord.Interaction, _):
        user = await bot.fetch_user(self.applicant_id)
        await user.send("❌ Ваша заявка была **отклонена**.")
        await interaction.message.edit(content="❌ Заявка отклонена!", view=None)

class ApplyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📩 Подать заявку", style=discord.ButtonStyle.primary)
    async def apply(self, interaction: discord.Interaction, _):
        await interaction.response.send_modal(ApplicationModal())

@bot.command()
async def send_application(ctx):
    embed = discord.Embed(
        title="📋 Подай заявку на модератора!",
        description=(
            "🔹 **Требования:**\n"
            "1️⃣ От 14 лет\n"
            "2️⃣ Опыт модерации\n"
            "3️⃣ Активность от 3 часов в день\n"
            "4️⃣ Знание правил\n"
            "5️⃣ Грамотная речь\n\n"
            "Нажмите кнопку ниже, чтобы подать заявку!"
        ),
        color=discord.Color.green()
    )
    await ctx.send(embed=embed, view=ApplyButton())

bot.run(TOKEN)
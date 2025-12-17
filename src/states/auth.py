#src/states/auth.py

from __future__ import annotations

import pygame
from typing import TYPE_CHECKING, Optional

from states.base import GameState
from ui.widgets import Button

if TYPE_CHECKING:
    from core.game import Game


class AuthState(GameState):
    """
    Login/Register ekranı.

    Mimari:
    - UI katmanı: AuthState (pygame input + ekranda çizim)
    - Data katmanı: UsersRepo (DB erişimi)
    - AuthState SQL bilmez, sadece repo metodlarını çağırır.

    UsersRepo API:
    - create_user(username, password) -> User
    - verify_login(username, password) -> Optional[User]
    - get_by_username(username) -> Optional[User]
    """

    def __init__(self, game: Game) -> None:
        super().__init__(game)

        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.label_font = pygame.font.SysFont("Arial", 22)
        self.input_font = pygame.font.SysFont("Consolas", 26)
        self.hint_font = pygame.font.SysFont("Arial", 18)
        self.button_font = pygame.font.SysFont("Arial", 26)

        # Input state
        self.username: str = ""
        self.password: str = ""
        self.active_field: str = "username"  # "username" | "password"

        # UI message
        self.message: str = ""
        self.message_color = (220, 90, 90)

        # Cursor blink
        self.cursor_visible = True
        self.cursor_timer = 0.0

        # Repo
        self.users_repo = self._get_users_repo()

        # Buttons
        self.buttons: list[Button] = []
        self._create_buttons()

    # ------------------------- Repo -------------------------

    def _get_users_repo(self):
        repo = getattr(self.game, "users_repo", None)
        if repo is not None:
            return repo

        try:
            from data.users_repo import UsersRepo
            return UsersRepo()
        except Exception:
            return None

    # ------------------------- UI Helpers -------------------------

    def _set_message(self, text: str, ok: bool) -> None:
        self.message = text
        self.message_color = (90, 220, 120) if ok else (220, 90, 90)

    def _normalize_username(self, raw: str) -> str:
        name = raw.strip()
        while "  " in name:
            name = name.replace("  ", " ")
        return name

    def _create_buttons(self) -> None:
        screen = self.game.screen
        w, h = screen.get_size()

        btn_w, btn_h = 200, 56
        spacing = 18
        center_x = w // 2

        base_y = (h // 2) + 130  # iki input kutusu var, biraz daha aşağı

        def make_rect(col: int) -> pygame.Rect:
            x = center_x + col * (btn_w + 16) - btn_w // 2
            y = base_y
            return pygame.Rect(x, y, btn_w, btn_h)

        def on_login():
            self._login()

        def on_register():
            self._register()

        def on_back():
            from states.menu import MenuState
            self.game.set_state(MenuState(self.game))

        self.buttons = [
            Button(make_rect(-1), "Login", on_login, self.button_font),
            Button(make_rect(1), "Register", on_register, self.button_font),
            Button(
                pygame.Rect(center_x - btn_w // 2, base_y + btn_h + spacing, btn_w, btn_h),
                "Back",
                on_back,
                self.button_font,
            ),
        ]

    # ------------------------- Core Auth -------------------------

    def _activate_user(self, user_obj) -> None:
        """
        UsersRepo, dataclass User döndürüyor:
        User(id, username, password_hash)
        """
        uid = getattr(user_obj, "id", None)
        uname = getattr(user_obj, "username", None)

        if uid is None:
            raise ValueError("User id could not be determined from repo result.")
        
        self.game.current_user_id = uid
        if uname is not None:
            self.game.current_username = uname


    def _go_next(self) -> None:
        """
        İstersen direkt Playing'e, istersen ThemeSelect'e.
        Şimdilik ThemeSelect bırakıyorum; direkt oynamak istersen aşağıyı değiştir.
        """
        from states.theme_select import ThemeSelectState
        self.game.set_state(ThemeSelectState(self.game))

        # Direkt Playing istersen:
        # from states.playing import PlayingState
        # self.game.set_state(PlayingState(self.game))

    def _login(self) -> None:
        if self.users_repo is None:
            self._set_message("UsersRepo bulunamadı (data/users_repo.py).", ok=False)
            return

        name = self._normalize_username(self.username)
        pwd = self.password

        if not name:
            self._set_message("Kullanıcı adı boş olamaz.", ok=False)
            return
        if not pwd:
            self._set_message("Şifre boş olamaz.", ok=False)
            return

        # Repo'nun gerçek login metodu
        user = self.users_repo.verify_login(name, pwd)
        if user is None:
            self._set_message("Login başarısız. Username/şifre yanlış.", ok=False)
            return

        self._activate_user(user)
        self._set_message(f"Giriş başarılı: {name}", ok=True)
        self._go_next()

    def _register(self) -> None:
        if self.users_repo is None:
            self._set_message("UsersRepo bulunamadı (data/users_repo.py).", ok=False)
            return

        name = self._normalize_username(self.username)
        pwd = self.password

        if not name:
            self._set_message("Kullanıcı adı boş olamaz.", ok=False)
            return
        if not pwd:
            self._set_message("Şifre boş olamaz.", ok=False)
            return

        # Önce var mı?
        existing = self.users_repo.get_by_username(name)
        if existing is not None:
            self._set_message("Bu kullanıcı adı zaten var. Login deneyin.", ok=False)
            return

        # Repo'nun gerçek create metodu: create_user(username, password)
        created_user = self.users_repo.create_user(name, pwd)

        self._activate_user(created_user)
        self._set_message(f"Kayıt başarılı: {name}", ok=True)
        self._go_next()

    # ------------------------- GameState Overrides -------------------------

    def enter(self) -> None:
        print("[AuthState] enter")
        self._set_message("TAB: alan değiştir | Enter: Login | Ctrl+Enter: Register", ok=True)

    def exit(self) -> None:
        print("[AuthState] exit")

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.game.running = False
            return

        if event.type == pygame.KEYDOWN:
            # ESC -> Menu
            if event.key == pygame.K_ESCAPE:
                from states.menu import MenuState
                self.game.set_state(MenuState(self.game))
                return

            # TAB -> username/password alanı değiştir
            if event.key == pygame.K_TAB:
                self.active_field = "password" if self.active_field == "username" else "username"
                return

            # Enter -> Login, Ctrl+Enter -> Register
            if event.key == pygame.K_RETURN:
                mods = pygame.key.get_mods()
                if mods & pygame.KMOD_CTRL:
                    self._register()
                else:
                    self._login()
                return

            # Backspace
            if event.key == pygame.K_BACKSPACE:
                if self.active_field == "username":
                    self.username = self.username[:-1]
                else:
                    self.password = self.password[:-1]
                return

            # Yazı girişi (printable)
            if event.unicode and event.unicode.isprintable():
                if self.active_field == "username":
                    if len(self.username) < 18:
                        self.username += event.unicode
                else:
                    if len(self.password) < 18:
                        self.password += event.unicode
                return

        # Buton click/hover eventleri
        for btn in self.buttons:
            btn.handle_event(event)

    def update(self, dt: float) -> None:
        for btn in self.buttons:
            btn.update(dt)

        # Cursor blink
        self.cursor_timer += dt
        if self.cursor_timer >= 0.5:
            self.cursor_timer = 0.0
            self.cursor_visible = not self.cursor_visible

    def render(self, surface: pygame.Surface) -> None:
        surface.fill((10, 12, 18))
        w, h = surface.get_size()

        # Title
        title = self.title_font.render("Login / Register", True, (230, 230, 255))
        surface.blit(title, title.get_rect(center=(w // 2, 110)))

        # Hint
        hint = self.hint_font.render("TAB ile alan değiştir. Enter=Login, Ctrl+Enter=Register", True, (170, 170, 190))
        surface.blit(hint, hint.get_rect(center=(w // 2, 155)))

        box_w, box_h = 420, 56

        # Username box
        user_rect = pygame.Rect(0, 0, box_w, box_h)
        user_rect.center = (w // 2, h // 2 - 45)

        user_label = self.label_font.render("Username", True, (210, 210, 210))
        surface.blit(user_label, (user_rect.x, user_rect.y - 28))

        pygame.draw.rect(surface, (30, 36, 52), user_rect, border_radius=10)
        border_col_user = (130, 150, 220) if self.active_field == "username" else (80, 90, 120)
        pygame.draw.rect(surface, border_col_user, user_rect, width=2, border_radius=10)

        user_text = self.username
        if self.active_field == "username" and self.cursor_visible:
            user_text += "|"
        user_surf = self.input_font.render(user_text, True, (245, 245, 245))
        surface.blit(user_surf, (user_rect.x + 14, user_rect.y + 12))

        # Password box
        pass_rect = pygame.Rect(0, 0, box_w, box_h)
        pass_rect.center = (w // 2, h // 2 + 35)

        pass_label = self.label_font.render("Password", True, (210, 210, 210))
        surface.blit(pass_label, (pass_rect.x, pass_rect.y - 28))

        pygame.draw.rect(surface, (30, 36, 52), pass_rect, border_radius=10)
        border_col_pass = (130, 150, 220) if self.active_field == "password" else (80, 90, 120)
        pygame.draw.rect(surface, border_col_pass, pass_rect, width=2, border_radius=10)

        masked_password = "*" * len(self.password)
        pass_text = masked_password
        if self.active_field == "password" and self.cursor_visible:
            pass_text += "|"
        pass_surf = self.input_font.render(pass_text, True, (245, 245, 245))
        surface.blit(pass_surf, (pass_rect.x + 14, pass_rect.y + 12))

        # Message
        if self.message:
            msg = self.label_font.render(self.message, True, self.message_color)
            surface.blit(msg, msg.get_rect(center=(w // 2, h // 2 + 95)))

        # Buttons
        for btn in self.buttons:
            btn.render(surface)

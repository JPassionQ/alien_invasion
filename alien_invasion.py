import sys
from time import sleep

import pygame

from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien


class AlienInvasion:
    """管理游戏资源和行为的类"""

    def __init__(self):
        """初始化游戏并创建游戏资源"""
        pygame.init()
        self.clock = pygame.time.Clock()
        self.settings = Settings()

        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height)
        )

        """
        全屏模式
        self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height
        """
        pygame.display.set_caption("Alien Invasion")

        # 创建一个用于存储游戏统计信息的实例
        self.stats = GameStats(self)
        # 创建存储游戏统计信息的实例，

        self.ship = Ship(self)
        # 创建用于存储子弹的编组
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()

        self._create_fleet()

        # 设置背景色
        self.bg_color = (230, 230, 230)

        # 游戏启动后处于活动状态
        self.game_active = False

        # 创建Play按钮
        self.play_button = Button(self, "Play")

    def run_game(self):
        """开始游戏的主循环"""
        while True:
            self._check_events()

            if self.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()

            self._update_screen()
            self.clock.tick(60)  # 循环1秒执行60次，也就是60帧

    def _check_events(self):
        """响应按键和鼠标事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_play_button(self, mouse_pos):
        """在玩家单击Play按钮时开始新游戏"""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.game_active:
            # 还原游戏设置
            self.settings.initialize_dynamic_settings()
            # 重置游戏的统计信息
            self.stats.reset_stats()
            self.game_active = True

            # 清空外星人列表和子弹列表
            self.bullets.empty()
            self.aliens.empty()

            # 创建一个新的外星舰队，并将飞船放在屏幕底部的中央
            self._create_fleet()
            self.ship.center_ship()

            # 隐藏光标 光标位于游戏窗口内时将其隐藏起来
            pygame.mouse.set_visible(False)

    def _check_keydown_events(self, event):
        """响应按下"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()

    def _check_keyup_events(self, event):
        """响应释放"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _fire_bullet(self):
        """创建一颗子弹，并将其加入编组bullets"""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        """更新子弹的位置并删除已经消失的子弹"""
        # 更新子弹的位置
        self.bullets.update()

        # 删除已消失的子弹
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        # 检查是否有子弹击中了外星人
        # 如果是，就删除相应的子弹和外星人
        # 返回一个字典，键值对：key：子弹，value：被击中的外星人
        # 两个值为True的参数表示在发生碰撞时删除对应的子弹和外星人
        # 高能子弹，第一个为False，第二个为True，即不删除子弹（key），只删除外星人（value）
        self._check_bullet_alien_collision()

    def _check_bullet_alien_collision(self):
        """响应子弹和外星人的碰撞"""
        # 删除发生碰撞的子弹和外星人
        collisions = pygame.sprite.groupcollide(
            self.bullets, self.aliens, True, True
        )
        if not self.aliens:
            # 删除现有的子弹并创建一个新的外星舰队
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

    def _update_aliens(self):
        """检查是否有外星人位于屏幕边缘，更新外星舰队中所有外星人的位置"""
        self._check_fleet_edges()
        self.aliens.update()

        # 检测外星人和飞船的碰撞
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        # 检查是否有外星人到达了屏幕下边缘
        self._check_alien_bottom()

    def _update_screen(self):
        """更新屏幕上的图像，并切换到新屏幕"""
        self.screen.fill(self.settings.bg_color)
        # 用静态的思维去考虑这个看似动态的事情
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.ship.blitme()
        self.aliens.draw(self.screen)

        # 如果游戏处于非活跃状态，就绘制Play按钮
        if not self.game_active:
            self.play_button.draw_button()

        pygame.display.flip()

    def _create_fleet(self):
        """创建一个外星舰队"""
        # 创建一个外星人 再不断添加 知道没有空间添加外星人为止
        # 外星人的间距为外星人的宽度和外星人的高度
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size

        current_x, current_y = alien_width, alien_height
        while current_y < (self.settings.screen_height - 3 * alien_height):
            while current_x < (self.settings.screen_width - 2 * alien_width):
                self._create_alien(current_x, current_y)
                current_x += 2 * alien_width

            # 添加一行外星人之后，重置x的值并递增y的值
            current_x = alien_width
            current_y += 2 * alien_width

    def _create_alien(self, x_position, y_position):
        """创建一个外星人并将其放在当前行中"""
        new_alien = Alien(self)
        new_alien.x = x_position
        new_alien.rect.x = x_position
        new_alien.rect.y = y_position
        self.aliens.add(new_alien)

    def _check_alien_bottom(self):
        """检查是否有外星人到达了屏幕的下边缘"""
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= self.settings.screen_height:
                # 像飞船被撞到一样进行处理
                self._ship_hit()
                break

    def _check_fleet_edges(self):
        """在有外星人到达边缘时采取相应的措施"""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """将整个外星舰队向下移动，并改变他们的方向"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1  # 改变方向

    def _ship_hit(self):
        """响应飞船和外星人的碰撞"""
        # 将ships_left减1
        if self.stats.ships_left > 0:
            self.stats.ships_left -= 1

            # 清空外星人列表和子弹列表
            self.aliens.empty()
            self.bullets.empty()

            # 创建一个新的外星人舰队，并将飞船放在屏幕底部的中央
            self._create_fleet()
            self.ship.center_ship()
            # 暂停
            sleep(0.5)
        else:
            self.game_active = False
            # 当游戏进入非活跃状态后，立刻让光标可见
            pygame.mouse.set_visible(True)


if __name__ == '__main__':
    # 创建游戏实例并运行游戏
    ai = AlienInvasion()
    ai.run_game()

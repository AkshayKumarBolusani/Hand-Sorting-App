import pygame
import math

def draw_rounded_rect(surface, rect, color, radius=20, border=0, border_color=(0,0,0)):
    x, y, w, h = rect
    shape_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, color, (radius, 0, w-2*radius, h))
    pygame.draw.rect(shape_surf, color, (0, radius, w, h-2*radius))
    pygame.draw.circle(shape_surf, color, (radius, radius), radius)
    pygame.draw.circle(shape_surf, color, (w-radius, radius), radius)
    pygame.draw.circle(shape_surf, color, (radius, h-radius), radius)
    pygame.draw.circle(shape_surf, color, (w-radius, h-radius), radius)
    if border > 0:
        pygame.draw.rect(shape_surf, border_color, (radius, 0, w-2*radius, h), border)
        pygame.draw.rect(shape_surf, border_color, (0, radius, w, h-2*radius), border)
    surface.blit(shape_surf, (x, y))

def draw_gradient(surface, rect, color1, color2, vertical=True):
    x, y, w, h = rect
    for i in range(h if vertical else w):
        color = [
            int(color1[j] + (float(i)/(h if vertical else w)) * (color2[j] - color1[j]))
            for j in range(3)
        ]
        if vertical:
            pygame.draw.line(surface, color, (x, y+i), (x+w, y+i))
        else:
            pygame.draw.line(surface, color, (x+i, y), (x+i, y+h))

def draw_shadow(surface, rect, shadow_color=(0,0,0,100), offset=(5,5), radius=20):
    x, y, w, h = rect
    shadow_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    draw_rounded_rect(shadow_surf, (0,0,w,h), shadow_color, radius)
    surface.blit(shadow_surf, (x+offset[0], y+offset[1]))

def animate_value(start, end, duration, elapsed):
    if elapsed >= duration:
        return end
    t = elapsed / duration
    return start + (end - start) * t 
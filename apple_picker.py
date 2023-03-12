import random
import pygame
import networkx as nx
import matplotlib.pyplot as plt

# Set up the game window
pygame.init()
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Apple Picker")

# Define some constants
good_apple_color = (0, 255, 0)
bad_apple_color = (255, 0, 0)
lever_color = (0, 0, 255)
laser_color = (200, 0, 0)
apple_radius = 20
lever_width = 100
lever_height = 10
apple_speed = 5
lever_speed = 10
game_duration = 120  # in seconds

max_lever_displacement = 20

# Define some variables
good_apple_count = 0
bad_apple_count = 0

bad_apple_value = -3
good_apple_value = 1
score = 0
game_start_time = pygame.time.get_ticks()

# Define some functions


def draw_laser_scan(x_pos, obstacle_height=0):
    pygame.draw.rect(screen, laser_color, (x_pos + lever_width /
                     2, obstacle_height, 1, screen_height))


def draw_lever(x_pos):
    pygame.draw.rect(screen, lever_color, (x_pos, screen_height -
                     lever_height, lever_width, lever_height))


def draw_apple(x_pos, y_pos, color):
    pygame.draw.circle(screen, color, (x_pos, y_pos), apple_radius)


def generate_apple():
    x_pos = random.randint(apple_radius, screen_width - apple_radius)
    y_pos = 0
    if random.random() < 0.2:  # 20% chance of generating a bad apple
        color = bad_apple_color
    else:
        color = good_apple_color
    return (x_pos, y_pos, color)


def detect_collision(apple, lever_pos):
    x_pos, y_pos, color = apple
    if y_pos + apple_radius >= screen_height - lever_height and x_pos >= lever_pos and x_pos <= lever_pos + lever_width:
        return True
    else:
        return False


def find_apple_in_laser_range(x_pos, apples):
    closest_apple = None
    lever_center = x_pos + lever_width/2
    for apple in apples:
        # Choose closest in height
        if abs(apple[0] - lever_center) < apple_radius:
            closest_apple = max(closest_apple, apple,
                                key=lambda a: 0 if a is None else a[1])

    return closest_apple


########################################################################
#
#
# Your code goes in this section below
# Avoid acessing global variables.
#
########################################################################

# World model should contain data and methods
# to represent and predict how the world works
class WorldModel:
    def __init__(self):
        # Grafo ponderado que conterá as informações das seções da tela a serem visitadas pelo agente
        # Cada seção será representada por um nó
        # As arestas do grafo terão o peso referente à distância de uma seção para outra
        self.graph = nx.Graph()

    def addNode(self, id, info={}):
        print(info)
        self.graph.add_node(id, info=info)

    def getNodes(self):
        return self.graph.nodes()

    def addEdge(self, node1, node2, weight):
        self.graph.add_edge(node1, node2, weight=weight)

    def getNodeByLeverPos(self, lever_pos):
        searched_node = None
        nodes = self.getNodes()
        for node in nodes:
            print(nodes[node]['info'])
            if(node == lever_pos):
                searched_node = node
        return searched_node

    def saveGraphImg(self):
        nx.draw(self.graph)
        plt.savefig('graph.png')

# Agent contains its reaction based on sensors and its understanding
# of the world. This is where you decide what action you take


class Agent:
    def __init__(self, wm, max_lever_displacement, arena_width):
        self.worlmodel = wm
        # O maximo de unidades que voce pode se mover na decisao
        self.max_lever_displacement = max_lever_displacement

        # Tamanho da arena
        self.arena_width = arena_width

        # Tamanho do cesto
        self.lever_width = lever_width

        # Limite direito da tela
        self.screen_right_pos_limit = arena_width - lever_width/2 - 1

        # Limite esquerdo da tela
        self.screen_left_pos_limit = 0 - lever_width/2

    # Essa função recebe dados dos sensores como argumento
    # e retorna o nova posicao. A nova posicao nao pode ser
    # mais distante que max_lever_displacement da anterior
    def decision(self, lever_pos, laser_scan, score):
        print(f"{lever_pos=}, {laser_scan=}, {score=}")

        info = {'laser_scan': laser_scan}
        nodes = self.worlmodel.getNodes()
        actual_node = None

        searched_node = self.worlmodel.getNodeByLeverPos(lever_pos)
        if(searched_node == None):
            self.worlmodel.addNode(lever_pos, info)
        else:
            nodes[searched_node]['info'] = info

        # Acessar a posição do mouse é apenas para facilitar depuração
        # a solução final não deve acessar os objetos ou funções do pygame

        # Armazena o limite máximo de movimentação do agente
        lever_movement_limit = self.lever_width/2 + self.max_lever_displacement

        # Representa o tamanho da seção da maçã
        apple_section_size = apple_radius * 2 - 1

        direction = 'right'
        desired_lever_pos = lever_pos

        if(direction == 'right'):
            desired_lever_pos = lever_pos + apple_section_size
            if(desired_lever_pos >= self.screen_right_pos_limit):
                desired_lever_pos = lever_pos
        elif(direction == 'left'):
            desired_lever_pos = lever_pos - apple_section_size
            if(desired_lever_pos < self.screen_left_pos_limit):
                desired_lever_pos = lever_pos

        if(self.worlmodel.getNodeByLeverPos(desired_lever_pos) == None):
            actual_node = self.worlmodel.getNodeByLeverPos(
                lever_pos)

            self.worlmodel.addNode(desired_lever_pos)
            desired_node = self.worlmodel.getNodeByLeverPos(
                desired_lever_pos)
            self.worlmodel.addEdge(
                actual_node, desired_node, desired_lever_pos - lever_pos)

        return desired_lever_pos


########################################################################
#
#
# Main game loop
#
#
########################################################################
wm = WorldModel()
agent = Agent(wm, max_lever_displacement, screen_width)

running = True
apples = []
lever_pos = int(0 - lever_width/2)
closest_apple = None
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear the screen
    screen.fill((255, 255, 255))

    closest_apple_distance = None
    if closest_apple is not None:
        closest_apple_distance = {
            "distance": (screen_height - lever_height) - closest_apple[1] - apple_radius,
            "color": "red" if closest_apple[2] == (255, 0, 0) else "green"
        }
    #print(f"{closest_apple_distance=} with data {closest_apple=}")
    desired_lever_pos = agent.decision(
        lever_pos, closest_apple_distance, score)
    if abs(lever_pos - desired_lever_pos) > lever_width/2 + max_lever_displacement:
        print("Max lever displacement exceeded")
    else:
        lever_pos = desired_lever_pos

    closest_apple = find_apple_in_laser_range(lever_pos, apples)

    draw_lever(lever_pos)
    draw_laser_scan(
        lever_pos, 0 if closest_apple is None else closest_apple[1])

    # Generate apples
    if random.random() < 0.05:  # 5% chance of generating an apple in each frame
        apple = generate_apple()
        if apple[2] == good_apple_color:
            good_apple_count += 1
        else:
            bad_apple_count += 1
        apples.append(apple)

    # Move apples and detect collisions
    novel_apples = []
    for idx, apple in enumerate(apples):
        x_pos, y_pos, color = apple
        y_pos += apple_speed
        if detect_collision(apple, lever_pos):
            if color == good_apple_color:
                score += good_apple_value
            else:
                score += bad_apple_value
        elif y_pos >= screen_height:
            pass
        else:
            novel_apples.append((x_pos, y_pos, color))
            draw_apple(x_pos, y_pos, color)
    apples = novel_apples

    # Draw the score
    score_text = "Score: " + str(score)
    font = pygame.font.SysFont("Arial", 32)
    score_surface = font.render(score_text, True, (0, 0, 0))
    screen.blit(score_surface, (10, 10))

    # Check if the game is over
    elapsed_time = (pygame.time.get_ticks() - game_start_time) / 1000
    if elapsed_time >= game_duration:
        running = False

    # Update the display
    pygame.display.update()
    pygame.time.wait(int(1000/30))

# Show the final score
final_score_text = "Final score: " + str(score)
print(f"score: {score}")
font = pygame.font.SysFont("Arial", 64)
final_score_surface = font.render(final_score_text, True, (0, 0, 0))
final_score_rect = final_score_surface.get_rect(
    center=(screen_width/2, screen_height/2))
screen.blit(final_score_surface, final_score_rect)
pygame.display.update()

# Wait for a few seconds before quitting
pygame.time.wait(3000)

# Quit the game
pygame.quit()

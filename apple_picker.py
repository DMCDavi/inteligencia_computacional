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
        self.graph = nx.Graph()
        self.apple_speed = apple_speed
        self.apple_radius = apple_radius
        # Representa o tamanho da seção da maçã
        self.apple_section_size = apple_radius * 2 - 1
        # Limite direito da tela
        self.screen_right_pos_limit = screen_width - lever_width/2 - 1
        # Limite esquerdo da tela
        self.screen_left_pos_limit = 0 - lever_width/2

        self.create_map()

    # Cria o "mapa" do mundo, composto pelas seções da maçã
    # Cada seção é representada pelo nó do grafo, e o id é sua primeira posição no eixo x
    # O peso da aresta é o tamanho da seção
    # Cada nó tem pelo menos uma aresta e no máximo duas
    def create_map(self):
        sections_positions = list(range(int(self.screen_left_pos_limit), int(self.screen_right_pos_limit), self.apple_section_size))
        for i in range(len(sections_positions)):
            self.add_node(sections_positions[i])
            if i > 0:
                self.add_edge(sections_positions[i - 1], sections_positions[i], self.apple_section_size)
        self.save_graph_img()

    def add_node(self, node_id, info=None):
        self.graph.add_node(node_id, info=info)

    def get_nodes(self):
        return self.graph.nodes()

    def add_edge(self, node1, node2, weight):
        self.graph.add_edge(node1, node2, weight=weight)

    def has_node(self, node):
        return self.graph.has_node(node)

    def set_node_info(self, node_id, info):
        if self.has_node(node_id):
            nodes = self.get_nodes()
            nodes[node_id]['info'] = info

    # Atualiza o estado do mundo após cada decisão
    # As maçãs caem uma certa quantidade de pixels após cada decisão
    def update_apples_distances(self):
        nodes = self.get_nodes()
        for node_id in nodes:
            info = nodes[node_id]['info']
            # As maçãs só desaparecem do mapa quando seu centro atinge o chão
            if info and info['distance'] > -self.apple_radius:
                info['distance'] -= self.apple_speed
            else:
                nodes[node_id]['info'] = None

    # Busca qual é a maçã que está mais próxima de cair no chão
    def search_closest_green_apple_to_ground(self):
        nodes = self.get_nodes()
        min_distance = None
        closest_green_apple = None
        for node in nodes:
            info = nodes[node]['info']
            if info and info['color'] == 'green':
                distance = info['distance']
                if min_distance is None or distance < min_distance:
                    min_distance = distance
                    closest_green_apple = node
        return closest_green_apple

    # Busca quais são as seções em que, a qualquer instante, é possível cair uma maçã vermelha
    def get_fallen_red_apples_sections(self):
        nodes = self.get_nodes()
        red_sections = []

        for apple_pos in nodes:
            info = nodes[apple_pos]['info']
            if info and info['color'] == 'red' and info['distance'] <= 10:
                # O cesto só captura se tocar no centro da maçã
                red_section = [apple_pos - (self.apple_radius - 1),
                               apple_pos + (self.apple_radius - 1)]
                red_sections.append(red_section)
        return red_sections

    # Retorna o caminho mais curto entre dois nós
    def get_shortest_path(self, source, target):
        shortest_path = nx.shortest_path(self.graph, source, target, weight='weight')
        shortest_path.remove(source)
        return shortest_path

    def save_graph_img(self):
        nx.draw(self.graph)
        plt.savefig('graph.png')

# Agent contains its reaction based on sensors and its understanding
# of the world. This is where you decide what action you take


class Agent:
    def __init__(self, wm, max_lever_displacement):
        self.worlmodel = wm
        # O maximo de unidades que voce pode se mover na decisao
        self.max_lever_displacement = max_lever_displacement
        # Tamanho do cesto
        self.lever_width = lever_width
        # Armazena o limite máximo de movimentação do agente
        self.lever_speed_limit = lever_width/2 + max_lever_displacement

    # Essa função recebe dados dos sensores como argumento
    # e retorna o nova posicao. A nova posicao nao pode ser
    # mais distante que max_lever_displacement da anterior
    def decision(self, lever_pos, laser_scan, score, closest_apple_path, direction):
        print(f"{lever_pos=}, {laser_scan=}, {score=}")

        desired_lever_pos = lever_pos
        self.worlmodel.set_node_info(lever_pos, laser_scan)

        # Caso ele já tenha calculado um caminho para capturar uma maçã verde, move por ele
        if len(closest_apple_path):
            desired_lever_pos = self.move_through_path(closest_apple_path)
        else:
            closest_apple = self.worlmodel.search_closest_green_apple_to_ground()
            # Verifica se a maçã mais próxima do chão está pronta para ser capturada
            if closest_apple and self.is_apple_ready_to_pick(closest_apple):
                # Calcula o menor caminho até a maçã
                closest_apple_path = self.worlmodel.get_shortest_path(lever_pos, closest_apple)
                if len(closest_apple_path):
                    desired_lever_pos = self.move_through_path(closest_apple_path)
            else:
                desired_lever_pos, direction = self.do_sweep(direction)

        red_sections = self.worlmodel.get_fallen_red_apples_sections()
        desired_lever_pos = self.avoid_red_sections(red_sections, desired_lever_pos)

        self.worlmodel.update_apples_distances()

        return desired_lever_pos, closest_apple_path, direction

    # Faz a varredura pelo mapa para coletar informações
    # Movimenta na forma de zigue-zague, percorre toda a direita e depois toda a esquerda
    def do_sweep(self, direction):
        desired_lever_pos = lever_pos

        if direction == 'right':
            desired_lever_pos = self.move_right(self.worlmodel.apple_section_size)
            if desired_lever_pos >= self.worlmodel.screen_right_pos_limit:
                desired_lever_pos = self.move_left(self.worlmodel.apple_section_size)
                direction = 'left'
        elif direction == 'left':
            desired_lever_pos = self.move_left(self.worlmodel.apple_section_size)
            if desired_lever_pos < self.worlmodel.screen_left_pos_limit:
                desired_lever_pos = self.move_right(self.worlmodel.apple_section_size)
                direction = 'right'

        return desired_lever_pos, direction

    def move_right(self, steps):
        return lever_pos + steps

    def move_left(self, steps):
        return lever_pos - steps

    def move_through_path(self, path):
        desired_lever_pos = path[0]
        path.remove(path[0])
        return desired_lever_pos

    # Verifica se é o momento certo de caminhar para pegar a maçã
    def is_apple_ready_to_pick(self, apple_pos):
        nodes = self.worlmodel.get_nodes()

        distance = nodes[apple_pos]['info']['distance']
        num_decisions_to_fall = distance/self.worlmodel.apple_speed

        lever_apple_distance = abs(apple_pos - lever_pos)
        num_decisions_to_reach = lever_apple_distance/self.worlmodel.apple_section_size

        if num_decisions_to_fall == num_decisions_to_reach - 1 or \
                num_decisions_to_fall == num_decisions_to_reach or \
                num_decisions_to_fall == num_decisions_to_reach + 1:
            return True
        return False

    # Evita que o agente vá para seções em que é possível pegar uma maçã vermelha
    def avoid_red_sections(self, red_sections, desired_lever_pos):
        if len(red_sections):
            lever_range = list(range(
                int(desired_lever_pos - self.lever_width / 2),
                int(desired_lever_pos + self.lever_width / 2))
            )
            for red_section in red_sections:
                red_section_range = list(range(red_section[0], red_section[1]))
                pixels_intersection = list(set(lever_range).intersection(set(red_section_range)))
                if len(pixels_intersection):
                    return lever_pos
        return desired_lever_pos

########################################################################
#
#
# Main game loop
#
#
########################################################################
wm = WorldModel()
agent = Agent(wm, max_lever_displacement)

running = True
apples = []
lever_pos = int(0 - lever_width/2)
closest_apple = None
shortest_path = []
direction = 'right'
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
    desired_lever_pos, shortest_path, direction = agent.decision(
        lever_pos, closest_apple_distance, score, shortest_path, direction)
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
        wm.save_graph_img()
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

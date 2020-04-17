from room import Room
from player import Player
from world import World

import random
from ast import literal_eval

class Queue():
    # copied from util.py
    def __init__(self):
        self.queue = []
    def enqueue(self, value):
        self.queue.append(value)
    def dequeue(self):
        if self.size() > 0:
            return self.queue.pop(0)
        else:
            return None
    def size(self):
        return len(self.queue)

# Load world
world = World()


# You may uncomment the smaller graphs for development and testing purposes.
# map_file = "maps/test_line.txt"
# map_file = "maps/test_cross.txt"
# map_file = "maps/test_loop.txt"
# map_file = "maps/test_loop_fork.txt"
map_file = "maps/main_maze.txt"

# Loads the map into a dictionary
room_graph=literal_eval(open(map_file, "r").read())
world.load_graph(room_graph)

# Print an ASCII map
world.print_rooms()

player = Player(world.starting_room)

# Fill this out with directions to walk
# traversal_path = ['n', 'n']
traversal_path = []

# traversal code start
connections = {}  # a running map of the world

world_map = {key: room_graph[key][1] for key in room_graph}
# print(world_map[0])

def add_current_room_to_conns():
    connections[player.current_room.id] = {}
    for direction in player.current_room.get_exits():
        next_room = getattr(player.current_room, f"{direction}_to")
        connections[player.current_room.id][direction] = next_room.id

def get_adj_ids(id):
    """Takes a room ID and returns the IDs of adjascent rooms"""
    results = []
    for direction in world_map[id]:
        results.append(world_map[id][direction])
    return results

def bfs(id):
    """Starting from given room id,
    return the sequence of rooms that will take them to
    the nearest unexplored room"""
    qq = Queue()
    qq.enqueue([id])
    visited = set()
    while qq.size() > 0:
        path = qq.dequeue()
        if path[-1] not in connections:
            return path
        if path[-1] not in visited:
            visited.add(path[-1])
            for next_room in get_adj_ids(path[-1]):
                new_path = path + [next_room]
                qq.enqueue(new_path)
    return []

def get_path(id):
    """Based on the room sequence from bfs,
    returns the series of cardinal directions to take
    to follow the path"""
    route = bfs(id)
    path = []
    for index, stop in enumerate(route[1:]):
        # note: the enumerate object itself is zero-indexed
        # previous stop id is route[index]
        # append the route[index] -> stop direction
        for direction in world_map[route[index]]:
            if world_map[route[index]][direction] == stop:
                path.append(direction)
    return path[::-1]

def is_branch(direction, current_room=None):
    if current_room is None:
        current_room = player.current_room
    starting_room = getattr(current_room, f"{direction}_to")
    # print(f"Checking whether {direction} is a branch from {current_room.id}")
    # return true if it is IMPOSSIBLE to get from starting_room to current room indirectly
    # do a BFS starting in starting_room looking for current_room
    # that excludes the direct edge
    # strategy: add the first layer to the queue "manually"
    qq = Queue()
    # qq.enqueue([starting_room.id])
    visited = set([starting_room.id])
    path = [starting_room.id]
    # enqueues all paths from starting_room that don't go back to current_room
    for next_room in get_adj_ids(path[-1]):
        if next_room != current_room.id:
            new_path = path + [next_room]
            qq.enqueue(new_path)
    while qq.size() > 0:
        path = qq.dequeue()
        # print(path)
        # print(visited)
        if path[-1] not in visited:
            visited.add(path[-1])
            # print(f"adj_ids to {path[-1]}: {get_adj_ids(path[-1])}")
            for next_room in get_adj_ids(path[-1]):
                if next_room == current_room.id:
                    # print(f"found loop {direction} of {current_room.id}")
                    return False
                new_path = [path] + [next_room]
                qq.enqueue(new_path)

    # if the search terminates without finding the current room, it's a branch
    # print(f"found branch {direction} of {current_room.id}")
    return True

set_path = []

def make_path():
    # main travel loop
    add_current_room_to_conns()
    while len(room_graph) > len(connections):

        # decide which direction to go
        door = None
        options = player.current_room.get_exits()
        # go through the first door that leads to a new room
        # minimal intervention to try for stretch: what if the choice is random?
        # strategy change: what if the player always went down dead ends when available
        # the test: if the next room LOOPS back to the starting room, deprioritize
        # real_options = []
        for option in options:
            if connections[player.current_room.id][option] not in connections:
                # print(f"checking {option} of {player.current_room.id}")
                if is_branch(option):
                    set_path = []
                    door = option
                    break

        # handle when all unstarted paths are loops
        # currently no good way to distinguish among different loops
        if door is None:
            for option in options:
                if connections[player.current_room.id][option] not in connections:
                    set_path = []
                    door = option
                    # real_options.append(option)
        # try:
        #     door = random.choice(real_options)
        # except IndexError:
        #     door = None

        # if all exits from a room have previously been explored
        if door is None:
            # BFS for the next unexplored room
            if len(set_path) == 0:
                set_path = get_path(player.current_room.id)
                # print(set_path)
            door = set_path[-1]
            set_path = set_path[:-1]
            

        # go
        # print(f"going {door}")
        player.travel(door)
        traversal_path.append(door)

        # if in a new room, mark it on the map
        if player.current_room.id not in connections:
            add_current_room_to_conns()

    # return traversal_path.copy()




# while True:
#     traversal_path = []
#     connections = {}
#     consider = make_path()
#     if len(traversal_path) < 970:
#         print(consider)
#         print(f"found traversal path {len(traversal_path)} long")
#         if len(traversal_path) < 960:
#             break
# print(consider)

make_path()

print(traversal_path)

# TRAVERSAL TEST
visited_rooms = set()
player.current_room = world.starting_room
visited_rooms.add(player.current_room)

for move in traversal_path:
    player.travel(move)
    visited_rooms.add(player.current_room)

if len(visited_rooms) == len(room_graph):
    print(f"TESTS PASSED: {len(traversal_path)} moves, {len(visited_rooms)} rooms visited")
else:
    print("TESTS FAILED: INCOMPLETE TRAVERSAL")
    print(f"{len(room_graph) - len(visited_rooms)} unvisited rooms")



#######
# UNCOMMENT TO WALK AROUND
#######
# player.current_room.print_room_description(player)
# while True:
#     cmds = input("-> ").lower().split(" ")
#     if cmds[0] in ["n", "s", "e", "w"]:
#         player.travel(cmds[0], True)
#     elif cmds[0] == "q":
#         break
#     else:
#         print("I did not understand that command.")

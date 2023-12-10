class Sprites:
    def __init__(self, tile_grid, num_of_tiles, group):
        self.position = 0
        self.tg = tile_grid
        self.num_of_tiles = num_of_tiles
        self.group = group

    def add_to_group(self):
        if self.tg not in self.group:
            self.group.append(self.tg)

    def remove_from_group(self):
        if self.tg in self.group:
            self.group.remove(self.tg)

    def update_tile(self, tile_position):
        self.tg[0] = tile_position

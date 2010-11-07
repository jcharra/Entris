
import random

LONG_INDICES = (1, 1, 1, 1),
T_INDICES = ((1, 1, 1), 
             (0, 1, 0))
HOOK1_INDICES = ((1, 1),
                 (1, 0),
                 (1, 0))
HOOK2_INDICES = ((1, 1),
                 (0, 1),
                 (0, 1))
BLOCK_INDICES = ((1, 1),
                 (1, 1))
FLASH1_INDICES = ((1, 0),
                  (1, 1),
                  (0, 1))
FLASH2_INDICES = ((0, 1),
                  (1, 1),
                  (1, 0))
DUCK_INDICES = ((0, 1, 1, 1, 0, 0),
                (1, 1, 0, 1, 0, 0),
                (0, 1, 1, 1, 0, 1),
                (1, 1, 1, 1, 1, 1),
                (1, 1, 1, 1, 1, 1),
                (0, 1, 1, 1, 1, 0))

# List of all parts available.
# The duck must be at index 0, as this is 
# associated with the duck probability.
PARTS = (DUCK_INDICES,
         LONG_INDICES, 
         T_INDICES,     
         HOOK1_INDICES, 
         HOOK2_INDICES, 
         BLOCK_INDICES,
         FLASH1_INDICES,
         FLASH2_INDICES)

def get_part_for_index(idx):
    return PARTS[idx]

def random_part_index_generator(duck_probability=0.1):
    while True:
        rand = random.random()
        if rand <= duck_probability:
            yield 0
        else:
            yield random.randint(1, len(PARTS) - 1)

def random_part_generator(duck_probability=0.1):
    """
    Yields parts randomly. The duck has a predefined probability
    that can be passed in as a parameter. The remaining probability
    is divided evenly among the other parts. 
    """
    index_gen = random_part_index_generator(duck_probability)
    while True:
        yield PARTS[index_gen.next()]
    
class Part(object):
    def __init__(self, template, row_width):
        self.template = template
        self.row_width = row_width
        self.position_index = 0
        self.color = self.choose_random_color()
        self.rotation_degree = 0
        self.rotations = self.build_rotation_dict()

    def build_rotation_dict(self):
        """
        Returns a dictionary mapping 0-3 to the rotations of
        the part by 0, 90, 180 and 270 degrees respectively.
        """
        current = self.template
        storage = {0: current}
        for i in range(1, 4):
            current = zip(*current[::-1])
            storage[i] = current
        return storage
            
    def choose_random_color(self):
        return (random.randint(40, 255),
                random.randint(40, 255),
                random.randint(40, 255))
        
    def get_indexes(self, added_rotation=0):
        """
        Returns the current indexes for the part.
        Rotation degrees 0 to 3 can be added to receive the indexes 
        for the part after corresponding rotation * 90 degrees.        
        """
        indexes = []
        degree = (self.rotation_degree + added_rotation) % 4
        matrix = self.rotations[degree]
        for idx, row in enumerate(matrix):
            for bit_idx, bit in enumerate(row):
                if bit:
                    indexes.append(self.position_index 
                                   + bit_idx 
                                   + idx * self.row_width)
        return indexes

    def rotation_degree_changed_by(self, degree, clockwise):
        delta = degree if clockwise else -degree
        return (self.rotation_degree + delta) % 4

    def rotate(self, degree, clockwise):
        self.rotation_degree = self.rotation_degree_changed_by(degree, clockwise)
        
        
if __name__ == '__main__':
    part_gen = random_part_generator(0.5)
    part_list = [part_gen.next() for i in range(1000)]
    assert part_list.count(DUCK_INDICES) > 400, "Abnormal deviation" 
    part_gen = random_part_generator(0.01)
    part_list = [part_gen.next() for i in range(1000)]
    assert part_list.count(DUCK_INDICES) > 5, "Abnormal deviation" 
        
        
        
        
        
        
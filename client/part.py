
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

PART_TEMPLATES = {LONG_INDICES: 1, 
                  T_INDICES: 1, 
                  HOOK1_INDICES: 1, 
                  HOOK2_INDICES: 1, 
                  BLOCK_INDICES: 1,
                  FLASH1_INDICES: 1,
                  FLASH2_INDICES: 1,
                  DUCK_INDICES: 1}

def random_part_generator(duck_probability=0.1):
    """
    Builds a dictionary mapping the pieces to their normed
    probabilities and yields pieces accordingly.
    
    The duck probability is handled specially and can be
    passed in as a parameter.
    """
    prob_dict = PART_TEMPLATES
    prob_dict[DUCK_INDICES] = duck_probability
    for k in prob_dict:
        if k != DUCK_INDICES:
            prob_dict[k] = (1 - duck_probability)/(len(prob_dict.keys()) - 1)
        
    total = float(sum(prob_dict.values()))
    normed_dict = dict((k, v/total) for k, v in prob_dict.items())
    
    # probability sum must not be too far from 1.0
    assert abs(sum(normed_dict.values()) - 1.0) < 0.01
    
    while True:
        current_sum = 0
        rfloat = random.random()
        for k in normed_dict:
            current_sum += normed_dict[k]
            if current_sum >= rfloat:
                yield k
                break
        else:
            # If, due to rounding errors, we have a total probability
            # sum < 1 and our random number is greater than this sum,
            # we need an appropriate fallback.
            yield max(normed_dict, key=lambda x: normed_dict[x])
    
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
        
        
        
        
        
        
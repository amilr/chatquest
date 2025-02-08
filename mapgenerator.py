import random

def generate_contiguous_shape(num_cells):
    """
    Generate a contiguous cluster of exactly num_cells cells.
    
    The algorithm starts at (0, 0) and then repeatedly adds a random neighbor
    (up, down, left, or right) of an already–included cell until the shape contains
    the desired number of cells. This ensures that all cells in the shape are contiguous.
    
    Returns:
        A sorted list (row-major order) of (row, col) tuples representing local coordinates.
    """
    shape = {(0, 0)}
    while len(shape) < num_cells:
        candidates = []
        for (r, c) in shape:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (r + dr, c + dc)
                if neighbor not in shape:
                    candidates.append(neighbor)
        if not candidates:
            break  # Should not happen unless num_cells == 0.
        shape.add(random.choice(candidates))
    
    # Normalize the shape so that the smallest row and col are 0.
    min_r = min(r for r, c in shape)
    min_c = min(c for r, c in shape)
    normalized = [(r - min_r, c - min_c) for r, c in shape]
    normalized.sort(key=lambda pos: (pos[0], pos[1]))
    return normalized

def generate_map(num_towns, min_places, max_places):
    """
    Generates a map, a dictionary mapping each town to its number of places,
    and returns the normalized grid coordinates of the cell "1:1".
    
    For each town:
      - A random number of places (cells) is chosen between min_places and max_places.
      - A contiguous shape is generated for these cells using generate_contiguous_shape.
      - Town 1 is placed arbitrarily at (0, 0); all other towns are docked to a cell
        adjacent to a previously–placed (parent) town to guarantee connectivity.
      - The new town’s shape is placed so that it does not overlap any existing cells.
    
    Returns:
        grid: A 2D list (array of arrays) where each cell is either an empty string ("")
              or a label "town:place" (e.g., "3:2").
        town_places: A dictionary mapping town number to the number of places.
        start_location: A tuple (x, y) indicating the normalized grid location of "1:1".
    """
    global_map = {}         # Mapping of (global_row, global_col) to cell label.
    town_cells_global = {}  # Mapping of town number to a set of global cell coordinates.
    town_places = {}        # Mapping of town number to the number of places.
    
    # For recording the global coordinate of "1:1"
    town1_first_global = None

    # Create a simple spanning tree to ensure connectivity:
    # Every town (except town 1) gets a random parent from among the already–placed towns.
    town_parent = {1: None}
    for town in range(2, num_towns + 1):
        parent = random.choice(list(range(1, town)))
        town_parent[town] = parent

    # Place towns one by one.
    for town in range(1, num_towns + 1):
        # Choose a random number of places for this town.
        num_places = random.randint(min_places, max_places)
        town_places[town] = num_places
        
        # Generate a contiguous shape for the town.
        shape = generate_contiguous_shape(num_places)
        
        # For town 1, we place it at (0, 0); for other towns, dock them near their parent.
        if town == 1:
            offset = (0, 0)
        else:
            parent = town_parent[town]
            parent_cells = list(town_cells_global[parent])
            random.shuffle(parent_cells)
            placed = False
            max_attempts = 200
            attempt = 0
            while not placed and attempt < max_attempts:
                attempt += 1
                # Pick a random cell from the parent's placed cells.
                pr, pc = random.choice(parent_cells)
                # Consider its four adjacent neighbors as candidate docking points.
                neighbors = [(pr - 1, pc), (pr + 1, pc), (pr, pc - 1), (pr, pc + 1)]
                random.shuffle(neighbors)
                for nbr in neighbors:
                    if nbr in global_map:
                        continue  # Candidate cell is already occupied.
                    # Try to align the town's shape so that one of its local cells falls on the neighbor.
                    for (lr, lc) in shape:
                        offset_candidate = (nbr[0] - lr, nbr[1] - lc)
                        # Check if placing the entire shape with this offset conflicts with existing cells.
                        conflict = False
                        for (r_local, c_local) in shape:
                            r_global = offset_candidate[0] + r_local
                            c_global = offset_candidate[1] + c_local
                            if (r_global, c_global) in global_map:
                                conflict = True
                                break
                        if not conflict:
                            offset = offset_candidate
                            placed = True
                            break
                    if placed:
                        break
            if not placed:
                raise RuntimeError(f"Could not place town {town} after many attempts.")

        # With the chosen offset, place the town's cells in the global map.
        placed_cells = set()
        for i, (r_local, c_local) in enumerate(shape):
            r_global = offset[0] + r_local
            c_global = offset[1] + c_local
            label = f"{town}:{i+1}"  # Label places as "town:place" (places are 1-indexed)
            global_map[(r_global, c_global)] = label
            placed_cells.add((r_global, c_global))
            # Record the location of "1:1" (first cell of town 1)
            if town == 1 and i == 0:
                town1_first_global = (r_global, c_global)
        town_cells_global[town] = placed_cells

    # Determine the grid boundaries.
    all_rows = [r for (r, _) in global_map.keys()]
    all_cols = [c for (_, c) in global_map.keys()]
    min_r, max_r = min(all_rows), max(all_rows)
    min_c, max_c = min(all_cols), max(all_cols)
    num_rows = max_r - min_r + 1
    num_cols = max_c - min_c + 1

    # Build the grid as a 2D list with empty strings where no town is placed.
    grid = [["" for _ in range(num_cols)] for _ in range(num_rows)]
    for (r, c), label in global_map.items():
        grid[r - min_r][c - min_c] = label

    # Compute the normalized coordinate of "1:1"
    # (i.e. adjust the global coordinate by the grid's minimum row and col)
    if town1_first_global is None:
        raise RuntimeError("Town 1's starting cell ('1:1') was not recorded.")
    start_location = (town1_first_global[1] - min_c + 1, town1_first_global[0] - min_r + 1)

    return grid, town_places, start_location

# Example usage:
if __name__ == "__main__":
    # Input parameters: number of towns, minimum places per town, maximum places per town.
    num_towns = 5
    min_places = 5
    max_places = 9

    grid, town_places, start_location = generate_map(num_towns, min_places, max_places)
    
    print("Generated Map Array:")
    for row in grid:
        print(str(row).replace("''", "'   '"))
    
    print("\nTown Places Dictionary:")
    print(town_places)
    
    print(f"\nThe normalized (x, y) location of '1:1' is: {start_location}")


class Counter:
  
  def __init__(self, threshold: float) -> None:
    self.threshold = threshold
    self.count = 0.0

  def get_updated_count(self, delta: float) -> float:
    self.count += delta
    c = self.count
    if self.count >= self.threshold:
      self.count = 0.0
    
    return c



from  base_service import BaseService
from app.repositories.category_repository import CategoryRepository
from app.models import Category
from sqlalchemy.orm import Session

class CategoryService(BaseService[Category]):
    def __init__(self, db: Session):
        self.post_repo = CategoryRepository(db)
        super().__init__(self.post_repo)

    def get_by_name(self, name:str) -> Optional[Category]:
        return self.get_by_name(uuid)

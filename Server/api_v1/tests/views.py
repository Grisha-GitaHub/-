from fastapi import APIRouter, HTTPException
from api_v1.tests import crud, schemas

router = APIRouter(tags=["Tests"])

@router.get("/", response_model=list[dict])
def list_tests():
    return crud.get_all_tests_metadata()

@router.get("/{test_id}", response_model=schemas.TestSchema)
def get_test(test_id: str):
    test = crud.get_test_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Тест не найден")
    return test
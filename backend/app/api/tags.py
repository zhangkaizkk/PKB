"""标签 API。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagResponse, TagUpdate

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagResponse])
def list_tags(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    return db.query(Tag).order_by(Tag.name).all()


@router.post("", response_model=TagResponse)
def create_tag(payload: TagCreate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    if db.query(Tag).filter(Tag.name == payload.name).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "标签已存在")
    tag = Tag(**payload.model_dump())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.patch("/{tag_id}", response_model=TagResponse)
def update_tag(tag_id: int, payload: TagUpdate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "标签不存在")
    update = payload.model_dump(exclude_unset=True)
    if update.get("name"):
        dup = db.query(Tag).filter(Tag.name == update["name"], Tag.id != tag_id).first()
        if dup:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "标签名已存在")
    for k, v in update.items():
        setattr(tag, k, v)
    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=204)
def delete_tag(tag_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "标签不存在")
    db.delete(tag)
    db.commit()

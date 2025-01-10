from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, List
from ..database import get_db
from ..auth import get_current_active_user, verify_guild_permissions
from ..models import AutoModRule as AutoModRuleModel
from ..schemas import (
    AutoModRule,
    AutoModRuleCreate,
    AutoModRuleUpdate,
    ErrorResponse
)

router = APIRouter(
    prefix="/api/automod",
    tags=["automod"],
    responses={401: {"model": ErrorResponse}}
)

@router.get("/{guild_id}/rules")
async def get_automod_rules(
    guild_id: str,
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all automod rules for a guild."""
    try:
        # Verify user has access to this guild
        await verify_guild_permissions(guild_id, current_user)

        # Get rules from database
        query = select(AutoModRuleModel).where(AutoModRuleModel.guild_id == guild_id)
        result = await db.execute(query)
        rules = result.scalars().all()

        return rules

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{guild_id}/rules", response_model=AutoModRule)
async def create_automod_rule(
    guild_id: str,
    rule: AutoModRuleCreate,
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new automod rule."""
    try:
        # Verify user has access to this guild
        await verify_guild_permissions(guild_id, current_user)

        # Create new rule
        new_rule = AutoModRuleModel(
            guild_id=guild_id,
            name=rule.name,
            type=rule.type,
            settings=rule.settings,
            enabled=rule.enabled
        )
        db.add(new_rule)
        await db.commit()
        await db.refresh(new_rule)

        return new_rule

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.put("/{guild_id}/rules/{rule_id}", response_model=AutoModRule)
async def update_automod_rule(
    guild_id: str,
    rule_id: int,
    rule_update: AutoModRuleUpdate,
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing automod rule."""
    try:
        # Verify user has access to this guild
        await verify_guild_permissions(guild_id, current_user)

        # Get existing rule
        query = select(AutoModRuleModel).where(
            AutoModRuleModel.id == rule_id,
            AutoModRuleModel.guild_id == guild_id
        )
        result = await db.execute(query)
        rule = result.scalar_one_or_none()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )

        # Update rule with new values
        for key, value in rule_update.dict(exclude_unset=True).items():
            setattr(rule, key, value)

        await db.commit()
        await db.refresh(rule)

        return rule

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{guild_id}/rules/{rule_id}")
async def delete_automod_rule(
    guild_id: str,
    rule_id: int,
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an automod rule."""
    try:
        # Verify user has access to this guild
        await verify_guild_permissions(guild_id, current_user)

        # Get existing rule
        query = select(AutoModRuleModel).where(
            AutoModRuleModel.id == rule_id,
            AutoModRuleModel.guild_id == guild_id
        )
        result = await db.execute(query)
        rule = result.scalar_one_or_none()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )

        # Delete rule
        await db.delete(rule)
        await db.commit()

        return {"message": "Rule deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{guild_id}/rules/{rule_id}/test")
async def test_automod_rule(
    guild_id: str,
    rule_id: int,
    test_message: Dict,
    current_user: Dict = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Test an automod rule against a sample message."""
    try:
        # Verify user has access to this guild
        await verify_guild_permissions(guild_id, current_user)

        # Get existing rule
        query = select(AutoModRuleModel).where(
            AutoModRuleModel.id == rule_id,
            AutoModRuleModel.guild_id == guild_id
        )
        result = await db.execute(query)
        rule = result.scalar_one_or_none()

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )

        # TODO: Test rule against message
        # This will be implemented when integrating with the Discord bot

        return {
            "would_trigger": True,  # Placeholder
            "matches": [],          # Placeholder
            "actions": []           # Placeholder
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

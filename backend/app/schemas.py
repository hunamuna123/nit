from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from app.core.catalog import Cover

Str = Annotated[str, StringConstraints(strip_whitespace=True)]
Role = Literal["learner", "expert", "admin"]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserBrief(ORM):
    id: int
    name: str
    role: Role
    expert_categories: list[str] = []


class UserMe(UserBrief):
    email: str
    bio: str
    expert_request_status: str | None
    created_at: datetime


class MeOut(BaseModel):
    user: UserMe | None


class RegisterIn(BaseModel):
    email: EmailStr
    name: Annotated[Str, Field(min_length=2, max_length=60)]
    password: Annotated[str, Field(min_length=6, max_length=128)]
    anon_id: str | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: Annotated[str, Field(min_length=1, max_length=128)]
    anon_id: str | None = None


class ProfileUpdateIn(BaseModel):
    name: Annotated[Str, Field(min_length=2, max_length=60)]
    bio: Annotated[Str, Field(max_length=400)] = ""


class ExpertRequestIn(BaseModel):
    categories: Annotated[list[str], Field(min_length=1, max_length=4)]
    text: Annotated[Str, Field(min_length=10, max_length=1000)]


class CategoryOut(BaseModel):
    slug: str
    title: str
    icon: str
    description: str
    count: int


class PlatformStats(BaseModel):
    guides: int
    steps: int
    runs: int
    completions: int
    learners: int
    authors: int


class ForkRef(BaseModel):
    id: int
    slug: str
    title: str
    author_name: str


class GuideCard(BaseModel):
    id: int
    slug: str
    title: str
    summary: str
    category: str
    tags: list[str]
    difficulty: int
    cover: str
    est_minutes: int
    steps_count: int
    author: UserBrief
    runs_count: int
    completions_count: int
    completion_rate: float
    rating: float | None
    rating_count: int
    usefulness: int
    verified: bool
    forked_from: ForkRef | None
    forks_count: int
    published_at: datetime | None
    snippet: str | None = None


class GuideList(BaseModel):
    items: list[GuideCard]
    total: int
    search_modes: list[str] = []


class ChecklistItem(BaseModel):
    key: str
    text: str


class StepOut(BaseModel):
    key: str
    position: int
    title: str
    body: str
    minutes: int
    checklist: list[ChecklistItem]


class VersionBrief(BaseModel):
    id: int
    number: int
    changelog: str
    published_at: datetime | None
    steps_count: int


class StepPublicStats(BaseModel):
    up: int = 0
    down: int = 0
    comments: int = 0
    my_vote: int | None = None


class RunState(BaseModel):
    checked: dict[str, list[str]] = {}
    done: list[str] = []


class RunBrief(BaseModel):
    id: str
    status: str
    current_step: int
    progress: float
    version_number: int
    outdated: bool


class GuideDetail(GuideCard):
    version: VersionBrief
    steps: list[StepOut]
    verified_by: UserBrief | None
    verified_at: datetime | None
    step_stats: dict[str, StepPublicStats]
    my_run: RunBrief | None
    my_rating: int | None
    bookmarked: bool
    is_author: bool
    versions_count: int


class RatingIn(BaseModel):
    value: Annotated[int, Field(ge=1, le=5)]
    review: Annotated[Str, Field(max_length=1000)] = ""


class RatingOut(BaseModel):
    rating: float | None
    rating_count: int
    my_rating: int


class VoteIn(BaseModel):
    step_key: Annotated[str, Field(max_length=36)]
    value: Literal[1, -1, 0]


class VoteOut(BaseModel):
    step_key: str
    up: int
    down: int
    my_vote: int | None


class BookmarkOut(BaseModel):
    bookmarked: bool


class CreatedOut(BaseModel):
    id: int
    slug: str


CommentKind = Literal["question", "tip", "comment"]


class CommentIn(BaseModel):
    step_key: Annotated[str | None, Field(max_length=36)] = None
    body: Annotated[Str, Field(min_length=1, max_length=2000)]
    kind: CommentKind = "comment"
    parent_id: int | None = None


class CommentOut(BaseModel):
    id: int
    step_key: str | None
    parent_id: int | None
    kind: str
    body: str
    created_at: datetime
    user: UserBrief
    is_author: bool


class SuggestionIn(BaseModel):
    step_key: Annotated[str, Field(max_length=36)]
    title: Annotated[Str | None, Field(max_length=200)] = None
    body: Annotated[Str, Field(min_length=1, max_length=20000)]
    message: Annotated[Str, Field(max_length=1000)] = ""


class SuggestionOut(BaseModel):
    id: int
    guide_id: int
    guide_slug: str
    guide_title: str
    step_key: str
    current_title: str | None
    current_body: str | None
    title: str | None
    body: str
    message: str
    status: str
    reply: str
    created_at: datetime
    resolved_at: datetime | None
    user: UserBrief


class SuggestionResolveIn(BaseModel):
    reply: Annotated[Str, Field(max_length=1000)] = ""


EventType = Literal["view", "complete", "stuck", "reopen"]


class RunEventIn(BaseModel):
    client_id: Annotated[str, Field(min_length=8, max_length=64)]
    type: EventType
    step_key: Annotated[str, Field(max_length=36)]
    duration_ms: Annotated[int | None, Field(ge=0, le=86_400_000)] = None
    at: datetime | None = None


class RunSyncIn(BaseModel):
    current_step: Annotated[int, Field(ge=0, le=1000)]
    state: RunState
    events: Annotated[list[RunEventIn], Field(max_length=300)] = []
    completed: bool = False


class RunOut(BaseModel):
    id: str
    guide_id: int
    guide_slug: str
    version_id: int
    version_number: int
    status: str
    current_step: int
    state: RunState
    started_at: datetime
    completed_at: datetime | None
    outdated: bool
    steps: list[StepOut]
    title: str


class HelpIn(BaseModel):
    step_key: Annotated[str, Field(max_length=36)]
    question: Annotated[Str, Field(max_length=600)] = ""


class HelpOut(BaseModel):
    hint: str | None
    tips: list[CommentOut]
    ai: bool


class ChecklistItemIn(BaseModel):
    key: Annotated[str | None, Field(max_length=36)] = None
    text: Annotated[Str, Field(min_length=1, max_length=300)]


class StepIn(BaseModel):
    key: Annotated[str | None, Field(max_length=36)] = None
    title: Annotated[Str, Field(max_length=200)]
    body: Annotated[str, Field(max_length=20000)] = ""
    minutes: Annotated[int, Field(ge=1, le=600)] = 5
    checklist: Annotated[list[ChecklistItemIn], Field(max_length=12)] = []


class EditorDocIn(BaseModel):
    title: Annotated[Str, Field(max_length=160)]
    summary: Annotated[Str, Field(max_length=600)] = ""
    category: str = "study"
    tags: Annotated[
        list[Annotated[Str, Field(min_length=1, max_length=40)]], Field(max_length=8)
    ] = []
    difficulty: Annotated[int, Field(ge=1, le=3)] = 1
    cover: Cover = "torus"
    steps: Annotated[list[StepIn], Field(max_length=40)] = []


class EditorDoc(BaseModel):
    id: int
    slug: str
    status: str
    title: str
    summary: str
    category: str
    tags: list[str]
    difficulty: int
    cover: str
    steps: list[StepOut]
    published_version: VersionBrief | None
    versions: list[VersionBrief]
    has_unpublished_changes: bool
    updated_at: datetime
    forked_from: ForkRef | None
    verified: bool
    open_suggestions: int


class PublishIn(BaseModel):
    changelog: Annotated[Str, Field(max_length=500)] = ""


class HotStep(BaseModel):
    key: str
    title: str
    score: int
    level: str


class StudioGuideItem(GuideCard):
    status: str
    has_unpublished_changes: bool
    open_suggestions: int
    hot_step: HotStep | None
    updated_at: datetime


class GuideDraftStep(BaseModel):
    title: str
    body: str
    minutes: int
    checklist: list[str]


class GuideDraft(BaseModel):
    title: str
    summary: str
    category: str
    tags: list[str]
    difficulty: int
    steps: list[GuideDraftStep]


class CreateGuideIn(BaseModel):
    title: Annotated[Str, Field(max_length=160)] = ""
    draft: GuideDraft | None = None


Level = Literal["ok", "warn", "critical"]


class StepAnalytics(BaseModel):
    key: str
    position: int
    title: str
    minutes: int
    reached: int
    completed: int
    dropped: int
    drop_rate: float
    median_seconds: float | None
    time_ratio: float | None
    up: int
    down: int
    stuck: int
    comments: int
    suggestions: int
    score: int
    level: Level
    reasons: list[str]
    prev_drop_rate: float | None


class AnalyticsTotals(BaseModel):
    runs: int
    completed: int
    active: int
    abandoned: int
    completion_rate: float
    median_total_minutes: float | None
    learners: int
    rating: float | None
    rating_count: int
    helpful_ratio: float | None


class DayPoint(BaseModel):
    day: date
    started: int
    completed: int


class VersionStat(BaseModel):
    id: int
    number: int
    published_at: datetime | None
    changelog: str
    runs: int
    completion_rate: float


class Analytics(BaseModel):
    guide_id: int
    title: str
    slug: str
    version: VersionBrief
    totals: AnalyticsTotals
    steps: list[StepAnalytics]
    timeline: list[DayPoint]
    versions: list[VersionStat]
    bottlenecks: list[str]


class InsightItem(BaseModel):
    step_key: str
    step_title: str
    diagnosis: str
    recommendation: str
    proposed_title: str
    proposed_body: str
    proposed_checklist: list[str]


class InsightsOut(BaseModel):
    summary: str
    items: list[InsightItem]


class AiDraftIn(BaseModel):
    topic: Annotated[Str, Field(min_length=3, max_length=300)]
    details: Annotated[Str, Field(max_length=2000)] = ""


class AiImportIn(BaseModel):
    text: Annotated[Str, Field(min_length=20, max_length=30000)]


class AiStepIn(BaseModel):
    title: Annotated[str, Field(max_length=200)]
    body: Annotated[str, Field(max_length=20000)] = ""
    checklist: Annotated[list[str], Field(max_length=12)] = []


class AiImproveIn(BaseModel):
    guide_title: Annotated[str, Field(max_length=160)] = ""
    step: AiStepIn
    mode: Literal["clarify", "simplify", "checklist", "expand", "custom"] = "clarify"
    instruction: Annotated[Str, Field(max_length=600)] = ""


class AiImproveOut(BaseModel):
    title: str
    body: str
    checklist: list[str]
    note: str


class AiReviewIn(BaseModel):
    title: Annotated[str, Field(max_length=160)]
    summary: Annotated[str, Field(max_length=600)] = ""
    steps: Annotated[list[AiStepIn], Field(max_length=40)]


class AiReviewIssue(BaseModel):
    step_index: int
    severity: Literal["high", "medium", "low"]
    message: str


class AiReviewOut(BaseModel):
    score: int
    verdict: str
    issues: list[AiReviewIssue]
    missing_steps: list[str]


class AiStatus(BaseModel):
    enabled: bool
    model: str
    remaining_hour: int


class ProfileStats(BaseModel):
    completed: int
    authored: int
    accepted_suggestions: int
    comments: int
    learners_helped: int


class ProfileOut(BaseModel):
    user: UserBrief
    bio: str
    created_at: datetime
    stats: ProfileStats
    guides: list[GuideCard]


class DashboardRun(BaseModel):
    run: RunBrief
    guide: GuideCard
    last_activity_at: datetime
    completed_at: datetime | None


class DashboardOut(BaseModel):
    active: list[DashboardRun]
    completed: list[DashboardRun]
    bookmarks: list[GuideCard]
    suggestions: list[SuggestionOut]


class ReviewQueueItem(BaseModel):
    guide: GuideCard
    version_number: int
    reason: Literal["new", "updated", "changes_requested"]


class ReviewIn(BaseModel):
    verdict: Literal["approved", "changes"]
    note: Annotated[Str, Field(max_length=1500)] = ""


class ReviewOut(BaseModel):
    id: int
    guide_id: int
    version_number: int
    verdict: str
    note: str
    created_at: datetime
    expert: UserBrief


class AdminUser(UserMe):
    guides_count: int
    expert_request_text: str | None
    expert_request_categories: list[str]


class AdminUserPatch(BaseModel):
    role: Role
    expert_categories: Annotated[list[str], Field(max_length=7)] = []


class AdminStats(BaseModel):
    users: int
    guides: int
    runs: int
    events: int
    ai_calls_24h: int
    ai_cost_24h: float
    ai_cost_total: float
    pending_expert_requests: int


class UploadOut(BaseModel):
    url: str

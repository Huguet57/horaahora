from pydantic import BaseModel

from backend.domain.content.group_directory import CastellerGroupDirectory


class CastellerGroupDirectorySchema(BaseModel):
    groups: list[str]
    revision: str
    official_url: str

    @classmethod
    def from_domain(cls, directory: CastellerGroupDirectory) -> "CastellerGroupDirectorySchema":
        return cls(
            groups=directory.groups,
            revision=directory.revision,
            official_url=directory.official_url,
        )

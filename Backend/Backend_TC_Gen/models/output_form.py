from typing import List, Literal
from pydantic import BaseModel

## Test Steps Model

class TestStepStatus(BaseModel):
    Step_Id: int
    Step_Name: str
    Feature: str
    Step_Status: Literal["Passing", "Non Passing"]


## High Level Test Case Model
class TestStep(BaseModel):
    Step_Name: str
    Step_Features: List[str]
    Step_Status: Literal["Passing", "Non Passing"]


class TestGroup(BaseModel):
    Test_Title: str
    Test_Steps: List[TestStep]
    Test_Status: Literal["Passing", "Non Passing"]


### Detailed Test Case Model

class DetailedTestStep(BaseModel):
    step: str
    Expected_Result: str


class TestCase(BaseModel):
    Test_Id: int
    Test_Name: str
    Test_Feature: str
    Test_Status: Literal["Passing", "Non Passing"]
    Detailed_Test_Steps: List[DetailedTestStep]

## US Linker Model

class USLinker(BaseModel):
    US: str
    relevant_conditions: str


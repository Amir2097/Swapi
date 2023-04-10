from typing import List

import aiohttp
import asyncio
from model import SwapiPeople, Base, Session, engine
from more_itertools import chunked
from aiohttp import ClientSession
import datetime


CHUNK_SIZE = 5


async def chunked_async(async_iter, size):

    buffer = []
    while True:
        try:
            item = await async_iter.__anext__()
        except StopAsyncIteration:
            if buffer:
                yield buffer
            break
        buffer.append(item)
        if len(buffer) == size:
            yield buffer
            buffer = []


def serialaizer(person):
    for key, value in person.items():
        if isinstance(value, List):
            person[key] = ','.join(value)
    return person


async def get_person(people_id: int, session: ClientSession):
    print(f'begin {people_id}')
    async with session.get(f'https://swapi.dev/api/people/{people_id}') as response:
        json_data = await response.json()
        serialized = serialaizer(json_data)
        serialized['id'] = people_id
    print(f'end {people_id}')
    return serialized


async def get_people():
    async with ClientSession() as session:
        for chunk in chunked(range(1, 11), CHUNK_SIZE):
            coroutines = [get_person(people_id=i, session=session) for i in chunk]
            results = await asyncio.gather(*coroutines)
            for item in results:
                if item.get('name'):
                    yield item


async def insert_people(people_chunk):
    async with Session() as session:
        session.add_all([SwapiPeople(
            id_hero=item.get('id'),
            birth_year=item.get('birth_year'),
            eye_color=item.get('eye_color'),
            gender=item.get('gender'),
            hair_color=item.get('hair_color'),
            height=item.get('height'),
            homeworld=item.get('homeworld'),
            mass=item.get('mass'),
            name=item.get('name'),
            films=item.get('films'),
            skin_color=item.get('skin_color'),
            species=item.get('species'),
            starships=item.get('starships'),
            vehicles=item.get('vehicles'),
        ) for item in people_chunk])
        await session.commit()


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()

    async for chunk in chunked_async(get_people(), CHUNK_SIZE):
        asyncio.create_task(insert_people(chunk))

    tasks = set(asyncio.all_tasks()) - {asyncio.current_task()}
    for task in tasks:
        await task


start = datetime.datetime.now()
asyncio.run(main())
print(datetime.datetime.now() - start)


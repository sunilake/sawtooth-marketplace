# Copyright 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

from marketplace_addressing import addresser
from marketplace_processor.protobuf import account_pb2
from marketplace_processor.protobuf import asset_pb2
from marketplace_processor.protobuf import holding_pb2
from marketplace_processor.protobuf import offer_pb2


class MarketplaceState(object):

    def __init__(self, context, timeout=2):
        self._context = context
        self._timeout = timeout
        self._state_entries = []

    def get_offer(self, identifier):
        address = addresser.make_offer_address(offer_id=identifier)

        self._state_entries.extend(self._context.get_state(
            addresses=[address],
            timeout=self._timeout))

        container = _get_offer_container(self._state_entries, address)
        offer = None
        try:
            offer = _get_offer_from_container(container, identifier)
        except KeyError:
            # We are fine with returning None
            pass

        return offer

    def set_create_offer(self,
                         identifier,
                         label,
                         description,
                         owners,
                         source,
                         source_quantity,
                         target,
                         target_quantity,
                         rules):
        address = addresser.make_offer_address(offer_id=identifier)
        container = _get_offer_container(self._state_entries, address)

        try:
            offer = _get_offer_from_container(container, identifier)

        except KeyError:
            offer = container.entries.add()

        offer.id = identifier
        offer.label = label
        offer.description = description
        offer.owners.extend(owners)
        offer.source = source
        offer.source_quantity = source_quantity
        offer.target = target
        offer.target_quantity = target_quantity
        offer.rules.extend(rules)
        offer.status = offer_pb2.Offer.OPEN

        state_entries_send = {}
        state_entries_send[address] = container.SerializeToString()
        return self._context.set_state(
            state_entries_send,
            self._timeout)

    def get_holding(self, identifier):
        address = addresser.make_holding_address(holding_id=identifier)

        self._state_entries.extend(self._context.get_state(
            addresses=[address],
            timeout=self._timeout))

        container = _get_holding_container(self._state_entries, address)

        holding = None
        try:
            holding = _get_holding_from_container(container, identifier)
        except KeyError:
            # Fine with returning None
            pass
        return holding

    def set_holding(self,
                    identifier,
                    label,
                    description,
                    account,
                    asset,
                    quantity):
        address = addresser.make_holding_address(holding_id=identifier)
        container = _get_holding_container(self._state_entries, address)

        try:
            holding = _get_holding_from_container(container, identifier)
        except KeyError:
            holding = container.entries.add()

        holding.id = identifier
        holding.label = label
        holding.description = description
        holding.account = account
        holding.asset = asset
        holding.quantity = quantity

        state_entries_send = {}
        state_entries_send[address] = container.SerializeToString()
        return self._context.set_state(
            state_entries_send,
            self._timeout)

    def get_asset(self, name):
        address = addresser.make_asset_address(asset_id=name)

        self._state_entries.extend(self._context.get_state(
            addresses=[address],
            timeout=self._timeout))

        container = _get_asset_container(self._state_entries, address)

        asset = None
        try:
            asset = _get_asset_from_container(container, name)
        except KeyError:
            # We are fine with returning None for an asset that doesn't exist
            pass
        return asset

    def set_asset(self, name, description, owners, rules):
        address = addresser.make_asset_address(name)

        container = _get_asset_container(self._state_entries, address)

        try:
            asset = _get_asset_from_container(container, name)
        except KeyError:
            asset = container.entries.add()

        asset.name = name
        asset.description = description
        asset.owners.extend(owners)
        asset.rules.extend(rules)

        state_entries_send = {}
        state_entries_send[address] = container.SerializeToString()
        return self._context.set_state(
            state_entries_send,
            self._timeout)

    def get_account(self, public_key):
        address = addresser.make_account_address(account_id=public_key)

        self._state_entries.extend(self._context.get_state(
            addresses=[address],
            timeout=self._timeout))

        container = _get_account_container(self._state_entries, address)
        account = None
        try:
            account = _get_account_from_container(
                container,
                identifier=public_key)
        except KeyError:
            # We are fine with returning None for an account that doesn't
            # exist in state.
            pass
        return account

    def set_account(self, public_key, label, description, holdings):
        address = addresser.make_account_address(account_id=public_key)

        container = _get_account_container(self._state_entries, address)

        try:
            account = _get_account_from_container(
                container,
                public_key)
        except KeyError:
            account = container.entries.add()

        account.public_key = public_key
        account.label = label
        account.description = description
        for holding in holdings:
            account.holdings.append(holding)

        state_entries_send = {}
        state_entries_send[address] = container.SerializeToString()
        return self._context.set_state(
            state_entries_send,
            self._timeout)

    def add_holding_to_account(self, public_key, holding_id):
        address = addresser.make_account_address(account_id=public_key)

        container = _get_account_container(self._state_entries, address)

        try:
            account = _get_account_from_container(
                container,
                public_key)
        except KeyError:
            account = container.entries.add()

        account.holdings.append(holding_id)

        state_entries_send = {}
        state_entries_send[address] = container.SerializeToString()
        return self._context.set_state(
            state_entries_send,
            self._timeout)


def _get_offer_container(state_entries, address):
    try:
        entry = _find_in_state(state_entries, address)
        container = offer_pb2.OfferContainer()
        container.ParseFromString(entry.data)
    except KeyError:
        container = offer_pb2.OfferContainer()

    return container


def _get_offer_from_container(container, offer_id):
    for offer in container.entries:
        if offer.id == offer_id:
            return offer
    raise KeyError(
        "Offer with id {} is not in container".format(offer_id))


def _get_holding_container(state_entries, address):
    try:
        entry = _find_in_state(state_entries, address)
        container = holding_pb2.HoldingContainer()
        container.ParseFromString(entry.data)
    except KeyError:
        container = holding_pb2.HoldingContainer()

    return container


def _get_holding_from_container(container, holding_id):
    for holding in container.entries:
        if holding.id == holding_id:
            return holding
    raise KeyError(
        "Holding with id {} is not in container".format(holding_id))


def _get_asset_container(state_entries, address):
    try:
        entry = _find_in_state(state_entries, address)
        container = asset_pb2.AssetContainer()
        container.ParseFromString(entry.data)
    except KeyError:
        container = asset_pb2.AssetContainer()
    return container


def _get_asset_from_container(container, name):
    for asset in container.entries:
        if asset.name == name:
            return asset
    raise KeyError(
        "Asset with name {} is not in container".format(name))


def _get_account_container(state_entries, address):
    try:
        entry = _find_in_state(state_entries, address)
        container = account_pb2.AccountContainer()
        container.ParseFromString(entry.data)
    except KeyError:
        container = account_pb2.AccountContainer()

    return container


def _get_account_from_container(container, identifier):
    for account in container.entries:
        if account.public_key == identifier:
            return account
    raise KeyError(
        "Account with identifier {} is not in container.".format(identifier))


def _find_in_state(state_entries, address):
    for entry in state_entries:
        if entry.address == address:
            return entry
    raise KeyError("Address {} not found in state".format(address))
